from datetime import datetime
import json
import sqlalchemy as sa
from llms.prompts import prompt_clean_up_text, prompt_text_to_structured_data
from orm import sa_sessionmaker
from recording.Recording import Recording
from recording.RecordingAnnotation import RecordingAnnotation


async def _pf_actor_action_recording_annotation(device_id: str, series_id: str, recording_id: int, type: str):
    print(f"[_pf_actor_action_recording_annotation] start: ", device_id)
    # RECORDING FETCH
    session = sa_sessionmaker()
    recording_query = await session.execute(sa.select(Recording).where(Recording.id == recording_id))
    recording = recording_query.scalars().unique().one()
    await session.close()
    print(f"[_pf_actor_action_recording_annotation] recording exists: {recording != None}")

    # PROCESS
    mark_type = type # set initial value from param
    # --- TODO: get type from transcript + image (do a relevant img grab )
    recording_annotation_base_payload = {
        "recording_id": recording_id,
        "device_id": device_id,
        "series_id": series_id,
        "created_at": datetime.now(),
        "type": mark_type,
    }
    
    # EXEC
    session = sa_sessionmaker()
    async with session.begin():
        # --- step header/description
        if mark_type == "step":
            transcript_text_refined = prompt_clean_up_text(recording.transcript_text, "Remove phrases like 'The next step is' since they provide no useful information")
            await session.execute(
                sa.insert(RecordingAnnotation).values({
                    **recording_annotation_base_payload,
                    "data": { "text": transcript_text_refined },
                }))
        # --- reminder
        elif mark_type == "reminder":
            transcript_text_refined = prompt_clean_up_text(recording.transcript_text)
            await session.execute(
                sa.insert(RecordingAnnotation).values({
                    **recording_annotation_base_payload,
                    "data": { "text": transcript_text_refined },
                }))
        # --- observation: gel electrophoresis (TODO: turn into structured data. save as JSON, but frontend could have export)
        elif mark_type == "observation.gel_electrophoresis":
            observation_params = prompt_text_to_structured_data(recording.transcript_text, "We are doing a gel electrophoresis which is described in the parameters of agrose percentage (described as decimals, ex: 0.01 instead of 1%), voltage, time duration, and number of lanes.", "{ gel_percentage?: decimal, voltage?: integer, duration?: integer, num_lanes?: integer  }")
            observation_data = prompt_text_to_structured_data(recording.transcript_text, f"We are doing a gel electrophoresis (params: {observation_params}), and we need to compile data about each 'lane' where our samples have been loaded and ran. Lanes can have multiple sample fragments that need to be recorded, for example a sliced piece of DNA that is now two fragments. Each fragment needs to be described as a JSON object within the lane array, with its base_pair length and an indicator of num_brightness (lets use 0 to 5 to describe this, 0 meaning not visible and 5 being clear and very bright). Ex: {{ 'lanes': {{ 'ladder': [], '1': [{{ label: 'plasmid', num_base_pairs: 13000, num_brightness: 3 }}], '2': [{{ label: 'ef1a', num_base_pairs: 700, num_brightness: 4 }}, {{ label: 'glargine', num_base_pairs: 300, num_brightness: 5 }}] }} }}", "{ 'lanes': {{ str: {{ label?: str, num_base_pairs?: int, num_brightness?: decimal; nanograms?: decimal }}[] }} }")
            await session.execute(
                sa.insert(RecordingAnnotation).values({
                    **recording_annotation_base_payload,
                    "data": { "observation_params": observation_params, "observation_data": observation_data },
                }))
        # --- observation: plate of microbial colonies (TODO: turn into structured data. save as JSON, but frontend could have export)
        elif mark_type == "observation.plate_colonies":
            await session.execute(
                sa.insert(RecordingAnnotation).values({
                    **recording_annotation_base_payload,
                    "data": {} # TODO: structure observation data
                }))
    # ... close 
    await session.close()


async def pf_actor_action_recording_annotation(job, job_token):
    print(f"[pf_actor_action_recording_annotation] start: ", job)
    try:
        # --- get params
        device_id = job.data.get("device_id")
        series_id = job.data.get("series_id")
        recording_id = job.data.get("recording_id")
        type = job.data.get("type")
        # --- strinigfy payload to transfer over the wire
        payload = await _pf_actor_action_recording_annotation(device_id, series_id, recording_id, type)
        return json.dumps(payload)
    except Exception as pf_err:
        print(f"[pf_actor_action_recording_annotation] error: ", pf_err)
        return None
