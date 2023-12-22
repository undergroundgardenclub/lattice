from datetime import datetime
import json
import sqlalchemy as sa
from orm import sa_sessionmaker
from recording.get_recording_file_duration import get_recording_file_duration
from recording.Recording import Recording
from voice.speech_to_text import speech_to_text


async def _pf_device_ingest_recording(media_file_dict: dict, device_id: str, series_id: str):
    """
    Process transcript for a recording file and save to database for later reference. TODO: could trigger follow up actions for passive analysis
    """
    print(f"[_pf_device_ingest_recording] device_id: {device_id}, series_id: {series_id}, file:", media_file_dict)
    
    # TRANSCRIBE
    transcript = speech_to_text(media_file_dict.get("file_url"), media_file_dict.get("transcript_id")) # transcript_id is only known if we've previously processed

    # DURATION (needed for offsetting image search, not a fan of slowing down processing/inserts but its simple for now)
    media_duration_sec = get_recording_file_duration(media_file_dict)

    # INSERT TO DB
    session = sa_sessionmaker()
    async with session.begin():
        await session.execute(
            sa.insert(Recording).values({
                "device_id": device_id,
                "series_id": series_id,
                "created_at": datetime.now(),
                "media_file_key": media_file_dict.get("file_key"),
                "media_file_url": media_file_dict.get("file_url"),
                "media_duration_sec": media_duration_sec,
                "transcript_id": transcript.get("transcript_id"),
                "transcript_text": transcript.get("text"),
                "transcript_sentences": transcript.get("sentences"),
                "transcript_words": transcript.get("words"),
            }))
    await session.close()

    # RETURN (??? maybe a recording db id)
    return


async def pf_device_ingest_recording(job, job_token):
    print(f"[pf_device_ingest_recording] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        series_id = job.data.get("series_id")
        media_file_dict = job.data.get("media_file_dict")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_device_ingest_recording(media_file_dict, device_id, series_id)
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_device_ingest_recording] error: ", pf_err)
        return None
