from datetime import datetime
import json
import sqlalchemy as sa
from orm import sa_sessionmaker
from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import get_media_duration, tmp_file_rmv, tmp_file_set
from intake.Recording import Recording
from voice.speech_to_text import speech_to_text


async def _job_intake_recording_series(file: dict, device_id: str, series_id: str):
    """
    Process transcript for a recording file and save to database for later reference. TODO: could trigger follow up actions for passive analysis
    """
    print(f"[_job_intake_recording_series] device_id: {device_id}, series_id: {series_id}, file:", file)
    
    # TRANSCRIBE
    transcript = speech_to_text(file.get("file_url"), file.get("transcript_id")) # transcript_id is only known if we've previously processed

    # DURATION (needed for offsetting image search, not a fan of slowing down processing/inserts but its simple for now)
    media_file_bytes = get_stored_file_bytes(file.get("file_key")) # TODO: request.files.get('file') but writing offline atm
    tmp_file_path = tmp_file_set(media_file_bytes) # need file path for OpenCV processing
    try:
        recording_duration_sec = get_media_duration(tmp_file_path)
    finally:
        tmp_file_rmv(tmp_file_path)

    # INSERT TO DB
    session = sa_sessionmaker()
    async with session.begin():
        await session.execute(
            sa.insert(Recording).values({
                "device_id": device_id,
                "series_id": series_id,
                "created_at": datetime.now(),
                "recording_file_key": file.get("file_key"),
                "recording_file_url": file.get("file_url"),
                "recording_duration_sec": recording_duration_sec,
                "transcript_id": transcript.get("transcript_id"),
                "transcript_text": transcript.get("text"),
                "transcript_sentences": transcript.get("sentences"),
                "transcript_words": transcript.get("words"),
            }))
    await session.close()

    # RETURN (??? maybe a recording db id)
    return


async def job_intake_recording_series(job, job_token):
    # --- get params
    device_id = job.data.get("device_id")
    series_id = job.data.get("series_id")
    file = job.data.get("file")
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_recording_series(file, device_id, series_id)
    return json.dumps(payload)
