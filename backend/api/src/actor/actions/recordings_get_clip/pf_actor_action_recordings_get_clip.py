from datetime import datetime, timedelta
import json
import sqlalchemy as sa
from emails.send_email import send_email
from orm import sa_sessionmaker
from recording.Recording import Recording
from recording.RecordingSeriesManager import RecordingSeriesManager


async def _pf_actor_action_recordings_get_clip(device_id: str, to_email: str, type: str, interval_unit: str = None, interval_num: int | str = None, step_description_text: str = None):
    # PARAMS (treating default as past 24 hours)
    if interval_unit  == "minutes":
        starting_time_for_scope = datetime.now() - timedelta(minutes=int(interval_num))
        ending_time_for_scope = datetime.now()  + timedelta(hours=2)
    elif interval_unit  == "hours":
        starting_time_for_scope = datetime.now() - timedelta(hours=int(interval_num))
        ending_time_for_scope = datetime.now() + timedelta(hours=2)
    elif interval_unit  == "days" and interval_num != 0: # this is just today basically, so do the 12 hr option
        starting_time_for_scope = datetime.now() - timedelta(days=int(interval_num))
        ending_time_for_scope = datetime.now() - timedelta(days=int(interval_num) + 1)
    else:
        starting_time_for_scope = datetime.now() - timedelta(hours=12) # asking for a 'step' 
        ending_time_for_scope = datetime.now()

    # RECORDINGS FETCH
    print(f"[_pf_actor_action_recordings_get_clip] fetching recordings: ", device_id, starting_time_for_scope, ending_time_for_scope)
    # --- query recordings
    recordings = []
    session = sa_sessionmaker()
    async with session.begin():
        query_recordings = await session.execute(
            sa.select(Recording)
                .where(sa.and_(
                    Recording.device_id == str(device_id),
                    Recording.created_at > starting_time_for_scope,
                    Recording.created_at < ending_time_for_scope,
                )) # TODO: include records that cover this time period, even if created_at, or save an end_at and just use that
                .order_by(Recording.id.asc()))
        recordings = query_recordings.scalars().unique().all()
    await session.close()
    # --- check if we have recordings
    if len(recordings) == 0:
        raise "No recordings found"

    # JOIN RECORDINGS
    print(f"[_pf_actor_action_recordings_get_clip] joining & sending: ", device_id)
    rsm = RecordingSeriesManager()
    try:
        await rsm.load_recordings(recordings)
        if type == "step": # if we're a step type, we need to filter down further based on annotations
            step_recordings = rsm.get_recordings_for_step(query_text=step_description_text)
            rsm.join_recordings(step_recordings)
            rsm.store_series_recording()
        else: # otherwise, just join all the recordings we grabbed earlier
            rsm.join_all_recordings()
            rsm.store_series_recording()
        # SEND EMAIL OF CLIP
        send_email(
            to_emails=[to_email],
            subject="Task Summary",
            html=f"<p>Video:<a href='{rsm.series_media_file_url}'>{rsm.series_media_file_url}</a></p>",
        )
    finally:
        rsm.remove_series_recording_file()


async def pf_actor_action_recordings_get_clip(job, job_token):
    print(f"[pf_actor_action_recordings_get_clip] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        type = job.data.get("type")
        interval_unit = job.data.get("interval_unit")
        interval_num = job.data.get("interval_num")
        to_email = job.data.get("to_email")
        step_description_text = job.data.get("step_description_text")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_actor_action_recordings_get_clip(device_id, to_email, type, interval_unit, interval_num, step_description_text)
        # --- allow access to completed payload
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_actor_action_recordings_get_clip] error: ", pf_err)
        return None
