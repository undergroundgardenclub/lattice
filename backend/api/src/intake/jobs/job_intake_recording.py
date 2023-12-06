import time
from emails.send_email import send_email
from emails.fill_email_template_html import fill_email_template_html_tasks_summary
from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_recording_transcript_to_task_headers, prompt_recording_transcript_to_task_outline
from voice.speech_to_text import speech_to_text
from vision.cv import video_frame_at_second


async def job_intake_recording(job, job_token):
    """
    Take a MP4 file, transcribe it, organize information into an outline, find relevant still image frames, and send update email
    """
    recording_file_key = job.data['file_key']
    recording_file_url = job.data['file_url']

    # --- transcribe (w/ timestamps on sections) -> text
    transcript = speech_to_text(recording_file_url)
    print(f"[intake_recording]", transcript['text'])
    
    # --- create outline of what occurred -> text[]
    session_task_headers = prompt_recording_transcript_to_task_headers(transcript['text'])
    print(f"[intake_recording]", session_task_headers)

    # BREAK: if no task headers, it's unclear that this video is of a protocol, skip processing/email
    if len(session_task_headers) == 0:
        return

    # --- for each outline sub-header write summary of what happened -> text[][]
    session_task_outline = prompt_recording_transcript_to_task_outline(transcript['sentences'], session_task_headers)
    print(f"[intake_recording]", session_task_outline)
    # session_task_outline = [{'taskName': 'Soldering', 'taskActions': ['Started soldering task', 'Mentioned concern about the dark environment'], 'taskStartAtSecond': 34, 'taskEndAtSecond': 54, 'taskThoughts': ['Sensor delay issue at the start', 'Video darkness issue']}, {'taskName': 'Setting Thermostat for Soldering Iron', 'taskActions': ['Set soldering iron to 375 degrees Celsius'], 'taskStartAtSecond': 54, 'taskEndAtSecond': 66, 'taskThoughts': []}, {'taskName': 'Drinking Halls Water', 'taskActions': ['Drank Halls water for palate'], 'taskStartAtSecond': 67, 'taskEndAtSecond': 78, 'taskThoughts': []}, {'taskName': 'Bathroom Break', 'taskActions': ['Took a bathroom break', "Contemplated whether to go 'number one or two'"], 'taskStartAtSecond': 79, 'taskEndAtSecond': 92, 'taskThoughts': ['Concerned about the sound sync and potential injury from soldering board']}]
    
    # --- grab image frames from time points and append to email sections (appending to dict because we need to create html img cid references and file data objs)
    video_file_bytes = get_stored_file_bytes(recording_file_key) # TODO: request.files.get('file') but writing offline atm
    tmp_file_path = tmp_file_set(video_file_bytes) # need file path for OpenCV processing
    try:
        for idx, task in enumerate(session_task_outline):
            taskSecondForImage = task['taskStartAtSecond']
            if task['taskEndAtSecond'] is not None:
                taskSecondForImage += ((task['taskEndAtSecond'] - task['taskStartAtSecond']) / 2)
            encoded_frame_jpg = video_frame_at_second(tmp_file_path, taskSecondForImage)
            if encoded_frame_jpg is not None:
                print(f"[intake_recording] image for sec. {taskSecondForImage}")
                session_task_outline[idx]['image'] = encoded_frame_jpg
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