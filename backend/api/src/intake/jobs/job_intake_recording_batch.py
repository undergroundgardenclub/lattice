import json
import numpy as np
import time
from typing import List
from emails.send_email import send_email
from emails.fill_email_template_html import fill_email_template_html_tasks_summary
from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_recording_transcript_to_task_headers, prompt_recording_transcript_to_task_outline
from voice.speech_to_text import speech_to_text
from vision.clip import clip_encode, clip_similarity
from vision.cv import encode_frame_to_jpg, video_frame_at_second, video_frame_generator

class RecordingSessionManager():
    # SETUP/PROPS
    recording_files = []
    recording_duration = 0
    transcripts = []
    transcript_text: str = "None"
    transcript_sentences = []
    transcript_words = []
    # LOADERS
    # --- loader: files -> transcripts -> text/sentences
    def load_recording_files(self, files) -> None:
        _transcripts = []
        for file in files:
            self.recording_files.append(file)
            transcript = speech_to_text(file['file_url'], file['transcript_id']) # transcript_id is only known if we've previously processed
            _transcripts.append(transcript)
        self.load_transcripts(_transcripts)
    # --- loader: transcripts -> text/sentences (this lacks the original reference files though :/)
    def load_transcripts(self, transcripts) -> None:
        # for each transcript
        for t_idx, t in enumerate(transcripts):
            # --- push to transcripts arr
            self.transcripts.append(t)
            # --- push to text/sentences props
            if t_idx == 0:
                self.transcript_text = ""
            self.transcript_text += t['text']
            # ... but map timings to prior transcript's last start/end
            last_transcript_end_second = transcripts[t_idx-1]['sentences'][-1]['second_end'] if t_idx > 0 else 0
            for s in t['sentences']:
                # --- append the recording file index to help grab video frames later
                s['recording_file_index'] = t_idx
                # --- update time positions for larger context
                s['adjusted_by_seconds'] = last_transcript_end_second
                s['adjusted_second_start'] = s['second_start'] + last_transcript_end_second
                s['adjusted_second_end'] = s['second_end'] + last_transcript_end_second
                self.transcript_sentences.append(s)
                # --- update duration length
                self.recording_duration = s['adjusted_second_end']
    # HELPERS
    # --- grab recording files after times were mapped
    def get_recording_file_at_adjusted_second(self, second: int) -> dict:
        for s in self.transcript_sentences:
            if s['adjusted_second_start'] <= second and s['adjusted_second_end'] >= second:
                return self.recording_files[s['recording_file_index']]
    def get_recorded_file_second_from_adjusted_second(self, second: int) -> int:
        for s in self.transcript_sentences:
            if s['adjusted_second_start'] <= second and s['adjusted_second_end'] >= second:
                return second - s['adjusted_by_seconds']
    # --- calcs
    def calc_second_between (self, second_start: int, second_end: int) -> int:
        return second_start + ((second_end - second_start) / 2)



async def _job_intake_recording_batch(files: List[dict]):
    """
    Take a list of MP4 files that represent a long session, transcribe/organize them, translate into an outline, send update email
    """

    rsm = RecordingSessionManager()
    # --- transcribe (w/ timestamps on sections) + map timings and things so there's larger context
    rsm.load_recording_files(files)
    
    # --- create outline of what occurred -> text[]
    session_task_headers = prompt_recording_transcript_to_task_headers(rsm.transcript_text)
    # BREAK: if no task headers, it's unclear that this video is of a protocol, skip processing/email
    if len(session_task_headers) == 0:
        return

    # --- for each outline sub-header write summary of what happened -> text[][]
    session_task_outline = prompt_recording_transcript_to_task_outline(rsm.transcript_sentences, session_task_headers)
    
    # --- grab image frames from time points and append to email sections (appending to dict because we need to create html img cid references and file data objs)
    for idx, task in enumerate(session_task_outline):

        # --- skip if no timestamps exist for task
        if task['taskStartAtSecond'] == None or task['taskEndAtSecond'] == None:
            continue

        # --- get task time point (we're getting it in seconds, but we've mapped the timings on our )
        recording_file = rsm.get_recording_file_at_adjusted_second(rsm.calc_second_between(task['taskStartAtSecond'], task['taskEndAtSecond']))
        # --- offset the task time so it's relative to the file (ex: a task starts 2 seconds into the 3rd recording. so task time may be 120s, but we need to start from 2s)
        recorded_task_start_second = rsm.get_recorded_file_second_from_adjusted_second(task['taskStartAtSecond'])
        recorded_task_end_second = rsm.get_recorded_file_second_from_adjusted_second(task['taskEndAtSecond'])
        print(f"[intake_recording_batch] task: {task['taskName']}, file key: {recording_file['file_key']}, recording start sec: {recorded_task_start_second}, recording end sec: {recorded_task_end_second}")

        # --- ensure that our task timings make sense since its a generative output
        if recorded_task_start_second >= recorded_task_end_second:
            continue
        if recorded_task_start_second > rsm.recording_duration or recorded_task_end_second > rsm.recording_duration:
            continue

        # --- grab video frame
        video_file_bytes = get_stored_file_bytes(recording_file['file_key']) # TODO: request.files.get('file') but writing offline atm
        tmp_file_path = tmp_file_set(video_file_bytes) # need file path for OpenCV processing
        try:
            # --- compile a frame for each second
            frames_for_comparison = []
            for frame in video_frame_generator(tmp_file_path, start_second=recorded_task_start_second, stop_second=recorded_task_end_second, interval_seconds=1):
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

async def job_intake_recording_batch(job, job_token):
    # --- get params
    files = job.data['files']
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_recording_batch(files)
    return json.dumps(payload)
