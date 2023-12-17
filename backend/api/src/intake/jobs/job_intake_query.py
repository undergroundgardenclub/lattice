from datetime import date, datetime, timedelta
import json
import sqlalchemy as sa
from sqlalchemy import func
from uuid import uuid4
from devices.DeviceMessage import DeviceMessage
from emails.send_email import send_email
from env import env_email_to_test
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from intake.Recording import Recording
from intake.recording_series_emailer import RecordingSeriesManager, recording_series_emailer
from llms.prompts import QueryTools, prompt_query_action, prompt_query_general_question_answer, prompt_query_help_manual
from orm import sa_sessionmaker
from voice.speech_to_text import speech_to_text
from voice.text_to_speech import text_to_speech
from vision.cv import video_frame_at_second


async def _job_intake_query(device_id: str, file: dict, text: str = None):
    """
    Take a MP4 file, analzye it to answer a question, generate speech audio, send that back
    """
    # INGEST
    # --- transcribe for query text
    transcript = speech_to_text(file.get("file_url"), file.get("transcript_id"))
    print(f"[job_intake_query]", transcript['text'])


    # INSTRUCT
    # --- ask for function type (series summary email, video slice request, query)
    query_tool_name, query_tool_args = prompt_query_action(transcript['text'])
    print(f"[job_intake_query] tool: {query_tool_name}", query_tool_args)


    # EXECUTE
    # --- summary email
    if query_tool_name == QueryTools().tools["send_recording_series_summary_email"]["name"]:
        # --- parse interval size/num off query args
        if query_tool_args["interval_unit"]  == "days":
            date_to_check = (datetime.now() - timedelta(days=query_tool_args["interval_num"])).date()
        else:
            raise f"Unexpected 'interval_unit': {query_tool_args['interval_unit']}"
        # --- query recordings
        recordings = []
        session = sa_sessionmaker()
        async with session.begin():
            query_recordings = await session.execute(
                sa.select(Recording)
                    .where(sa.and_(
                        Recording.device_id == str(device_id),
                        func.date(Recording.created_at) == date_to_check
                    ))
                    .order_by(Recording.id.asc()))
            recordings = query_recordings.scalars().unique().all()
        await session.close()
        # --- check if we have recordings
        if len(recordings) == 0:
            raise "No recordings found"
        # --- summarize & email
        recording_series_emailer(recordings, env_email_to_test())


    # --- video series composition
    elif query_tool_name == QueryTools().tools["send_video_series_slice"]["name"]:
        # --- parse interval size/num off query args
        if query_tool_args["interval_unit"]  == "minutes":
            starting_time_for_scope = datetime.now() - timedelta(minutes=query_tool_args["interval_num"])
        elif query_tool_args["interval_unit"]  == "hours":
            starting_time_for_scope = datetime.now() - timedelta(hours=query_tool_args["interval_num"])
        else:
            raise f"Unexpected 'interval_unit': {query_tool_args['interval_unit']}"
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
        # --- join/cut/upload video
        rsm = RecordingSeriesManager()
        rsm.load_recordings(recordings)
        try:
            rsm.join_recordings()
            rsm.store_series_recording()
            # --- send email of clip
            send_email(
                to_emails=[env_email_to_test()],
                subject="Task Summary",
                html=f"<p>Video:<a href='{rsm.series_recording_file_url}'>{rsm.series_recording_file_url}</a></p>",
            )
        finally:
            rsm.remove_series_recording_file()


    # --- question answer
    elif query_tool_name == QueryTools().tools["question_answer"]["name"]:
        # --- get frame (going to grab 2 seconds in for simplicity)
        video_file_bytes = get_stored_file_bytes(file.get("file_key"))
        tmp_file_path = tmp_file_set(video_file_bytes, "mp4")
        try:
            encoded_frame_jpg = video_frame_at_second(tmp_file_path, 1)
        finally:
            tmp_file_rmv(tmp_file_path)
        # --- query gpt
        answer_text = prompt_query_general_question_answer(transcript['text'], encoded_frame_jpg)
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
        # --- return
        payload = { 'file_url': response_audio_file_url }
        print(f"[job_intake_query] payload: ", payload)
        return payload


    # --- describe manaul of what can be asked
    elif query_tool_name == QueryTools().tools["help_manual_about_tool"]["name"]:
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
        print(f"[job_intake_query] payload: ", payload)
        return payload


    # --- other (this exists to ensure LLM doesn't push into prior categories)
    else:
        print("[job_intake_query] tool '{query_tool}' unexpected")



async def job_intake_query(job, job_token):
    # --- get params
    device_id = job.data.get("device_id")
    file = job.data.get("file")
    text = job.data.get("text")
    # --- strinigfy payload to transfer over the wire
    payload = await _job_intake_query(device_id, file, text)
    return json.dumps(payload)
