from datetime import datetime
import json
import sqlalchemy as sa
from uuid import uuid4
from device.DeviceMessage import DeviceMessage
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_query_general_question_answer, prompt_query_help_manual
from orm import sa_sessionmaker
from recording.Recording import Recording
from vision.cv import video_frame_at_second
from voice.text_to_speech import text_to_speech


async def _pf_actor_action_question_answer(device_id: str, series_id: str, recording_id: dict):
    print(f"[_pf_actor_action_question_answer] start: ", device_id)
    # RECORDING FETCH
    session = sa_sessionmaker()
    recording_query = await session.execute(sa.select(Recording).where(Recording.id == recording_id))
    recording = recording_query.scalars().unique().one()
    print(f"[_pf_actor_action_question_answer] recording exists: {recording != None}")

    # PROCESS
    # --- get frame (going to grab 2 seconds in for simplicity)
    video_file_bytes = get_stored_file_bytes(recording.media_file_key)
    tmp_file_path = tmp_file_set(video_file_bytes, "mp4")
    try:
        encoded_frame_jpg = video_frame_at_second(tmp_file_path, 1)
    finally:
        tmp_file_rmv(tmp_file_path)
    # --- query gpt
    answer_text = prompt_query_general_question_answer(recording.transcript_text, encoded_frame_jpg)
    print(f"[_pf_actor_action_question_answer] answer_text: {answer_text}")

    # RESPOND (via device message polling)
    # --- text to speech
    response_audio_bytes = text_to_speech(answer_text)
    # --- save file to S3 for reference
    response_audio_key = f"{uuid4()}.mp3"
    store_file_from_bytes(response_audio_bytes, response_audio_key)
    response_audio_file_url = get_stored_file_url(response_audio_key)
    # --- device message for playback
    session = sa_sessionmaker()
    async with session.begin():
        await session.execute(
            sa.insert(DeviceMessage).values({
                "device_id": device_id,
                "type": "play_audio",
                "data": json.dumps({ "file_url": response_audio_file_url }),
                "created_at": datetime.now(),
            }))
    await session.close()

    # RETURN job
    payload = { 'file_url': response_audio_file_url }
    return payload


async def pf_actor_action_question_answer(job, job_token):
    print(f"[pf_actor_action_question_answer] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        series_id = job.data.get("series_id")
        recording_id = job.data.get("recording_id")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_actor_action_question_answer(device_id, series_id, recording_id)
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_actor_action_question_answer] error: ", pf_err)
        return None
