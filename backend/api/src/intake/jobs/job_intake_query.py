import json
from uuid import uuid4
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_query
from voice.speech_to_text import speech_to_text
from voice.text_to_speech import text_to_speech
from vision.cv import video_frame_at_second


async def _job_intake_query(recording_file_key: str, recording_file_url: str):
    """
    Take a MP4 file, analzye it to answer a question, generate speech audio, send that back
    """
    # --- transcribe for question text
    transcript = speech_to_text(recording_file_url)
    print(f"[job_intake_query]", transcript['text'])
    # --- get frame (going to grab 2 seconds in for simplicity)
    video_file_bytes = get_stored_file_bytes(recording_file_key)
    tmp_file_path = tmp_file_set(video_file_bytes)
    try:
        encoded_frame_jpg = video_frame_at_second(tmp_file_path, 1)
    finally:
        tmp_file_rmv(tmp_file_path)
    # --- query gpt
    answer_text = prompt_query(transcript['text'], encoded_frame_jpg)
    # --- text to speech
    answer_audio_bytes = text_to_speech(answer_text)
    # --- save file to S3 for reference
    answer_audio_key = f"{uuid4()}.mp3"
    answer_audio_file_url = get_stored_file_url(answer_audio_key)
    store_file_from_bytes(answer_audio_bytes, answer_audio_key)
    # --- return narration
    payload = { 'file_url': answer_audio_file_url }
    print(f"[job_intake_query] payload: ", payload)
    return payload


async def job_intake_query(job, job_token):
    # --- get params
    recording_file_key = job.data['file_key']
    recording_file_url = job.data['file_url']
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_query(recording_file_key, recording_file_url)
    return json.dumps(payload)
