import json
import numpy as np
import time
from emails.send_email import send_email
from emails.fill_email_template_html import fill_email_template_html_tasks_summary
from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_recording_transcript_to_task_headers, prompt_recording_transcript_to_task_outline
from voice.speech_to_text import speech_to_text
from vision.clip import clip_encode, clip_similarity
from vision.cv import encode_frame_to_jpg, video_frame_at_second, video_frame_generator


async def _job_intake_recording(recording_file_key: str, recording_file_url: str):
    """
    Take a MP4 file, transcribe it, organize information into an outline, find relevant still image frames, and send update email
    """

    # --- transcribe (w/ timestamps on sections) -> text
    transcript = speech_to_text(recording_file_url)
    print(f"[intake_recording]", transcript['text'])
    
    # --- create outline of what occurred -> text[]
    session_task_headers = prompt_recording_transcript_to_task_headers(transcript['text'])
    # BREAK: if no task headers, it's unclear that this video is of a protocol, skip processing/email
    if len(session_task_headers) == 0:
        return

    # --- for each outline sub-header write summary of what happened -> text[][]
    session_task_outline = prompt_recording_transcript_to_task_outline(transcript['sentences'], session_task_headers)
    print(f"[intake_recording]", session_task_outline)
    # session_task_outline = [{'taskName': 'Soldering', 'taskSummary': 'Task involving soldering components.', 'taskActions': ['Setting soldering iron to 375 degrees Celsius.'], 'taskObservation': 'After soldering, the individual moves on to the next task.', 'taskStartAtSecond': 34, 'taskEndAtSecond': 66}, {'taskName': 'Drink Halls Water', 'taskSummary': 'Task involving drinking Halls water.', 'taskActions': ['Drinking Halls water to refresh palate.'], 'taskObservation': 'The individual drinks Halls water after soldering.', 'taskStartAtSecond': 67, 'taskEndAtSecond': 78}, {'taskName': 'Bathroom Break', 'taskSummary': 'Task involving a bathroom break.', 'taskActions': ['Going to the bathroom for either a one or two.'], 'taskObservation': 'The individual contemplates the sound sync while concerned about the board melting to their skin.', 'taskStartAtSecond': 79, 'taskEndAtSecond': 92}]
    
    # --- grab image frames from time points and append to email sections (appending to dict because we need to create html img cid references and file data objs)
    video_file_bytes = get_stored_file_bytes(recording_file_key) # TODO: request.files.get('file') but writing offline atm
    tmp_file_path = tmp_file_set(video_file_bytes) # need file path for OpenCV processing
    try:
        for idx, task in enumerate(session_task_outline):
            # --- skip if no timestamps exist for task
            if task['taskStartAtSecond'] == None or task['taskEndAtSecond'] == None:
                continue
            # --- compile a frame for each second
            frames_for_comparison = []
            for frame in video_frame_generator(tmp_file_path, start_second=task['taskStartAtSecond'], stop_second=task['taskEndAtSecond'], interval_seconds=1):
                frames_for_comparison.append(frame)
            # --- encode frames with CLIP, as well as task summary to find most associated image for task preview/snapshot
            image_encodings, text_encodings = clip_encode(frames_for_comparison, [task['taskSummary']])
            # --- eval cosine similarity
            image_similarities = clip_similarity(image_encodings, text_encodings[0]) # returns a list of 0 to 1 values mapping to list arg
            highest_image_similarity_idx = np.argmax(image_similarities) # grab index of highest value so we can select for it
            # --- compress frame
            frame_encoded_as_jpg = encode_frame_to_jpg(frames_for_comparison[highest_image_similarity_idx]) # compress data (for email)
            # --- associate the best pick with the session obj
            session_task_outline[idx]['image'] = frame_encoded_as_jpg
    finally:
        tmp_file_rmv(tmp_file_path)

    # --- convert summary into HTML for email
    email_html = fill_email_template_html_tasks_summary(session_task_outline)

    # --- send email
    send_email(
        to_emails=["x@markthemark.com"],
        subject="Task Summary",
        html=email_html
    )
    print(f"[intake_recording] sent email")

    # --- return something?
    return

async def job_intake_recording(job, job_token):
    # --- get params
    recording_file_key = job.data['file_key']
    recording_file_url = job.data['file_url']
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_recording(recording_file_key, recording_file_url)
    return json.dumps(payload)
