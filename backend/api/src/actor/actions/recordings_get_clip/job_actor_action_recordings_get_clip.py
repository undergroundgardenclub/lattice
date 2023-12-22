from datetime import datetime, timedelta
import json
import sqlalchemy as sa
from emails.send_email import send_email
from orm import sa_sessionmaker
from recording.Recording import Recording
from recording.RecordingSeriesManager import RecordingSeriesManager


async def _job_actor_action_recordings_get_clip(device_id: str, series_id: str, interval_unit: str, interval_num: int, to_email: str):
    # PARAMS
    # --- parse interval size/num off query args
    if interval_unit  == "minutes":
        starting_time_for_scope = datetime.now() - timedelta(minutes=interval_num)
    elif interval_unit  == "hours":
        starting_time_for_scope = datetime.now() - timedelta(hours=interval_num)
    else:
        raise f"Unexpected 'interval_unit': {interval_unit}"

    # RECORDINGS FETCH
    print(f"[_job_actor_action_recordings_get_clip] fetching recordings: ", device_id)
    # --- query recordings
    recordings = []
    session = sa_sessionmaker()
    async with session.begin():
        query_recordings = await session.execute(
            sa.select(Recording)
                .where(sa.and_(
                    Recording.device_id == str(device_id),
                    # TODO: include records that cover this time period, even if created_at, or save an end_at and just use that
                    Recording.created_at > starting_time_for_scope
                ))
                .order_by(Recording.id.asc()))
        recordings = query_recordings.scalars().unique().all()
    await session.close()
    # --- check if we have recordings
    if len(recordings) == 0:
        raise "No recordings found"

    # JOIN & SEND RECORDINGS
    print(f"[_job_actor_action_recordings_get_clip] joining & sending: ", device_id)
    # --- join/cut/upload video
    rsm = RecordingSeriesManager()
    try:
        rsm.load_recordings(recordings)
        rsm.join_recordings()
        rsm.store_series_recording()
        # --- send email of clip
        send_email(
            to_emails=[to_email],
            subject="Task Summary",
            html=f"<p>Video:<a href='{rsm.series_media_file_url}'>{rsm.series_media_file_url}</a></p>",
        )
    finally:
        rsm.remove_series_recording_file()


async def job_actor_action_recordings_get_clip(job, job_token):
    print(f"[job_actor_action_recordings_get_clip] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        series_id = job.data.get("series_id")
        interval_unit = job.data.get("interval_unit")
        interval_num = job.data.get("interval_num")
        to_email = job.data.get("to_email")
        # --- strinigfy payload to transfer over the wire
        payload = await _job_actor_action_recordings_get_clip(device_id, series_id, interval_unit, interval_num, to_email)
        # --- allow access to completed payload
        return json.dumps(payload)
    except Exception as job_err:
        print(f"[job_actor_action_recordings_get_clip] error: ", job_err)
        return None
