import json
import sqlalchemy as sa
from orm import sa_sessionmaker
from intake.Recording import Recording
from intake.recording_series_emailer import recording_series_emailer


async def _job_intake_recording_series_done(device_id: str, series_id: str):
    """
    Process a 'series' of recordings to output a summary email
    """
    print(f"[_job_intake_recording_series_done] device_id: {device_id}, series_id: {series_id}")

    # FETCH RECORDINGS
    recordings = []
    session = sa_sessionmaker()
    async with session.begin():
        query_recordings = await session.execute(
            sa.select(Recording)
                .where(sa.and_(Recording.device_id == str(device_id), Recording.series_id == str(series_id)))
                .order_by(Recording.id.asc()))
        recordings = query_recordings.scalars().unique().all()
    await session.close()

    # SUMMARIZE & EMAIL
    recording_series_emailer(recordings, "x@markthemark.com")

    # RETURN (??? maybe a recording db id)
    return


async def job_intake_recording_series_done(job, job_token):
    # --- get params
    device_id = job.data.get("device_id")
    series_id = job.data.get("series_id")
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_recording_series_done(device_id, series_id)
    return json.dumps(payload)
