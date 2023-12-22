from datetime import datetime
import json
import sqlalchemy as sa
from uuid import uuid4
from device.DeviceMessage import DeviceMessage
from file.file_cloud_storage import get_stored_file_url, store_file_from_bytes
from llms.prompts import prompt_query_help_manual
from orm import sa_sessionmaker
from voice.text_to_speech import text_to_speech


async def _pf_actor_action_describe_device_manual(device_id: str):
    # --- query stringified tools dict with their descriptions/SON schemas
    help_manual_text = prompt_query_help_manual()
    # --- text to speech
    response_audio_bytes = text_to_speech(help_manual_text)
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
    # --- return
    payload = { 'file_url': response_audio_file_url }
    print(f"[_pf_actor_action_describe_device_manual] payload: ", payload)
    return payload


async def pf_actor_action_describe_device_manual(job, job_token):
    print(f"[pf_actor_action_describe_device_manual] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_actor_action_describe_device_manual(device_id)
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_actor_action_describe_device_manual] error: ", pf_err)
        return None
