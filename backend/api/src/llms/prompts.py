import json
import yaml
from typing import List
from openai import OpenAI
from guidance import models
from env import env_open_ai_api_key


openai_client = OpenAI(api_key=env_open_ai_api_key())

def prompt_recording_transcript_to_task_headers(transcript) -> List[str]:
    # query OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant designed to output JSON of a protocol with the schema, { protocolTaskHeaders: string[] }. Given an audio transcript, list out the headlines for this protocol. Details are not for this step. Example) { protocolTaskHeaders: ['Gather Reagents', 'Heat Shock Plasmids into E.Coli', 'Plate Cells', 'Incubate Cells'] }" },
            { "role": "user", "content": transcript }
        ],
        temperature=0.2,
    )
    # parse response
    data = json.loads(response.choices[0].message.content)
    headers = data['protocolTaskHeaders']
    print(f"[prompt_recording_transcript_to_task_headers] headers: {headers}")
    # return
    return headers

def prompt_recording_transcript_to_task_outline(transcript: str, task_headers: List[str]):
    # query OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant designed to output JSON of a protocol with the schema, { protocolTasks: { taskName: str; taskActions: str[]; taskStartAtSecond?: int; taskEndAtSecond?: int; taskThoughts: str[] }[] }. Given an audio transcript as YML and task names as an array string, associate actions and observations mentioned in the transcript with each as an array of task objects. Example) { protocolTasks: [{ taskName: 'Gather Reagents', taskActions: ['Took competent cells out of -80C freezer', 'Took ampicilin out of -20C freezer.'], taskStartAtSecond: 0, taskEndAtSecond: 10, taskThoughts: [] }, { taskName: 'Heat Shock Plasmids into E.Coli', taskActions: ['Heat shocked cells at 42C in water bath'], taskStartAtSecond: 14, taskEndAtSecond: 80 taskThoughts: [] }, { taskName: 'Plate Cells', taskActions: ['Plate 100µl of cells on 2 AMP plates', 'Plated 200µl of cells on 2 AMP plates'], taskStartAtSecond: 80, taskEndAtSecond: 10, taskThoughts: ['Plates look weird, did we use the right agar?'] }, { taskName: 'Incubate Cells', taskActions: ['Placed all plates in incubator at 37C'], taskStartAtSecond: 120, taskEndAtSecond: null, taskThoughts: ['Incubator temperature gauge seemed finiky'] }] }" },
            # converting to YML because its considered fewer tokens
            { "role": "user", "content": f"Task Names: {task_headers}\n\nTranscript YML:\n\n{yaml.dump(transcript)}" }
        ],
        temperature=0.2,
    )
    # parse response
    data = json.loads(response.choices[0].message.content)
    tasks = data['protocolTasks']
    print(f"[prompt_recording_transcript_to_task_headers] num tasks: {len(tasks)}")
    # return
    return tasks
