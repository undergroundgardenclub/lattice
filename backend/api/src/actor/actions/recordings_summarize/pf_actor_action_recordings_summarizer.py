from datetime import datetime, timedelta
import json
import sqlalchemy as sa
from sqlalchemy import func
from actor.actions.recordings_summarize.recordings_html_summarizer import recordings_html_summarizer
from emails.send_email import send_email
from orm import sa_sessionmaker
from recording.Recording import Recording


async def _pf_actor_action_recordings_summarizer(device_id: str, interval_unit: str, interval_num: int, to_email: str):
    # PARAMS
    if interval_unit  == "days":
        date_to_check = (datetime.now() - timedelta(days=interval_num)).date()
    else:
        date_to_check = datetime.now().date()
    # QUERY RECORDINGS
    print(f"[_pf_actor_action_recordings_summarizer] querying recordings on date: {date_to_check}")
    recordings = []
    session = sa_sessionmaker()
    async with session.begin():
        query_recordings = await session.execute(
            sa.select(Recording)
                .where(sa.and_(
                    Recording.device_id == str(device_id),
                    func.date(Recording.created_at) == date_to_check
                    # TODO: should probably filter out recordings without a series (ex: stray questions asked outside of recordings get roped in)
                ))
                .order_by(Recording.id.asc()))
        recordings = query_recordings.scalars().unique().all()
    await session.close()
    print(f"[_pf_actor_action_recordings_summarizer] got {len(recordings)} recordings")
    # --- check if we have recordings
    if len(recordings) == 0:
        raise "No recordings found"
    # SUMMARIZE
    summary_html = await recordings_html_summarizer(recordings)
    print(f"[_pf_actor_action_recordings_summarizer] summarized recordings")
    # EMAIL
    send_email(
        to_emails=[to_email],
        subject="Task Summary",
        html=summary_html
    )


async def pf_actor_action_recordings_summarizer(job, job_token):
    print(f"[pf_actor_action_recordings_summarizer] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        interval_unit = job.data.get("interval_unit")
        interval_num = job.data.get("interval_num")
        to_email = job.data.get("to_email")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_actor_action_recordings_summarizer(device_id, interval_unit, interval_num, to_email)
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_actor_action_recordings_summarizer] error: ", pf_err)
        return None
