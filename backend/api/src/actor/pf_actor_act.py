from datetime import datetime
import json
from typing import Optional
import sqlalchemy as sa
from env import env_email_to_test
from recording.get_recording_file_duration import get_recording_file_duration
from recording.Recording import Recording
from llms.prompts import prompt_determine_actor_tool
from actor.actor_tools import ActorTools
from queues.queues import queues
from queues.queue_add_job import queue_add_job
from orm import sa_sessionmaker
from voice.speech_to_text import speech_to_text


async def _pf_actor_act(device_id: str, series_id: str, query_media_file_dict: dict, query_text: Optional[str]):
    """
    Do something based on what a person sent in
    """
    # INGEST
    _query_text = query_text
    # --- transcribe for query text if none provided and file passed in
    if query_media_file_dict != None:
        transcript = speech_to_text(query_media_file_dict.get("file_url"), query_media_file_dict.get("transcript_id"))
        _query_text = transcript["text"]
    # --- save recording to db before exiting (TODO: refactor this w/ series file?)
    media_duration_sec = get_recording_file_duration(query_media_file_dict)
    session = sa_sessionmaker()
    async with session.begin():
        recording_query = await session.execute(
            sa.insert(Recording).values({
                "device_id": device_id,
                "series_id": series_id,
                "created_at": datetime.now(),
                "media_file_key": query_media_file_dict.get("file_key"),
                "media_file_url": query_media_file_dict.get("file_url"),
                "media_duration_sec": media_duration_sec,
                "transcript_id": transcript.get("transcript_id"),
                "transcript_text": transcript.get("text"),
                "transcript_sentences": transcript.get("sentences"),
                "transcript_words": transcript.get("words"),
            }).returning(Recording.id))
        recording_id = recording_query.scalar_one_or_none()
    await session.close()

    # INSTRUCT
    # --- ask for function type (series summary email, video slice request, query)
    print(f"[_pf_actor_act] query: ", _query_text)
    query_tool_name, query_tool_args = prompt_determine_actor_tool(_query_text)
    print(f"[_pf_actor_act] tool: {query_tool_name}", query_tool_args)

    # EXECUTE
    at = ActorTools()
    # --- describe manaul of what can be asked
    if query_tool_name == at.tools["help_manual_about_tool"]["name"]:
        await queue_add_job(queues['actor_action_describe_device_manual'], {
            "device_id": device_id,
        })
    # --- question answer
    elif query_tool_name == at.tools["question_answer"]["name"]:
        await queue_add_job(queues['actor_action_question_answer'], {
            "device_id": device_id,
            "series_id": series_id, # not used btw
            "recording_id": recording_id,
        })
    # --- summary email
    elif query_tool_name == at.tools["send_recording_series_summary_email"]["name"]:
        await queue_add_job(queues['actor_action_recordings_summarizer'], {
            "device_id": device_id,
            "series_id": series_id, # not used btw
            "interval_unit": query_tool_args["interval_unit"],
            "interval_num": int(query_tool_args["interval_num"]),
            "to_email": env_email_to_test()
        })
    # --- video series composition
    elif query_tool_name == at.tools["send_video_series_slice"]["name"]:
        await queue_add_job(queues['actor_action_recordings_get_clip'], {
            "device_id": device_id,
            "series_id": series_id, # not used btw
            "interval_unit": query_tool_args["interval_unit"],
            "interval_num": int(query_tool_args["interval_num"]),
            "to_email": env_email_to_test()
        })
    # --- other (this exists to ensure LLM doesn't push into prior categories)
    else:
        print("[_pf_actor_act] tool '{query_tool}' unexpected")


async def pf_actor_act(job, job_token):
    print(f"[pf_actor_act] start", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        series_id = job.data.get("series_id")
        query_media_file_dict = job.data.get("query_media_file_dict")
        query_text = job.data.get("query_text")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_actor_act(device_id, series_id, query_media_file_dict, query_text)
        # --- allow access to payload data on completed jobs
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_actor_act] error: ", pf_err)
        return None
