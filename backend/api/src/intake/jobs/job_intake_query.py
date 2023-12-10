from datetime import datetime
import json
import sqlalchemy as sa
from uuid import uuid4
from devices.DeviceMessage import DeviceMessage
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_query
from orm import sa_sessionmaker
from voice.speech_to_text import speech_to_text
from voice.text_to_speech import text_to_speech
from vision.cv import video_frame_at_second


async def _job_intake_query(device_id: str, file: dict, text: str = None):
    """
    Take a MP4 file, analzye it to answer a question, generate speech audio, send that back
    """
    # INGEST
    # --- transcribe for question text
    transcript = speech_to_text(file.get("file_url"), file.get("transcript_id"))
    print(f"[job_intake_query]", transcript['text'])
    # --- get frame (going to grab 2 seconds in for simplicity)
    video_file_bytes = get_stored_file_bytes(file.get("file_key"))
    tmp_file_path = tmp_file_set(video_file_bytes)
    try:
        encoded_frame_jpg = video_frame_at_second(tmp_file_path, 1)
    finally:
        tmp_file_rmv(tmp_file_path)

    # PROCESS
    # --- query gpt
    answer_text = prompt_query(transcript['text'], encoded_frame_jpg)
    # --- text to speech
    answer_audio_bytes = text_to_speech(answer_text)
    # --- save file to S3 for reference
    answer_audio_key = f"{uuid4()}.mp3"
    answer_audio_file_url = get_stored_file_url(answer_audio_key)
    store_file_from_bytes(answer_audio_bytes, answer_audio_key)

    # INSERT DEVICE MESSAGES (devices can retrieve these)
    session = sa_sessionmaker()
    async with session.begin():
        await session.execute(
            sa.insert(DeviceMessage).values({
                "device_id": device_id,
                "type": "play_audio",
                "data": json.dumps({ "file_url": answer_audio_file_url }),
                "created_at": datetime.now(),
            }))
    await session.close()

    # RETURN
    payload = { 'file_url': answer_audio_file_url }
    print(f"[job_intake_query] payload: ", payload)
    return payload


async def job_intake_query(job, job_token):
    # --- get params
    device_id = job.data.get("device_id")
    file = job.data.get("file")
    text = job.data.get("text")
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_query(device_id, file, text)
    return json.dumps(payload)
