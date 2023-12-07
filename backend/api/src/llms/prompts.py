import json
import numpy as np
import yaml
from typing import List
from openai import OpenAI
from env import env_open_ai_api_key
from vision.cv import encoded_frame_to_base64


openai_client = OpenAI(api_key=env_open_ai_api_key())

def prompt_recording_transcript_to_task_headers(transcript) -> List[str]:
    # query
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
    # query
    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant designed to output JSON annotating lab work/protocols with the schema, { protocolTasks: { taskName: str; taskSummary: str; taskActions: str[]; taskStartAtSecond?: int; taskEndAtSecond?: int; }[] }. Given an audio transcript as YML and task names as an array string, associate actions and observations mentioned in the transcript with each as an array of task objects." },
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

def prompt_query(question_text: str, question_image_arr: np.ndarray):
    print(f"[prompty_query] querying")
    # encode image
    base64_image = encoded_frame_to_base64(question_image_arr)
    # query
    response = openai_client.chat.completions.create(
        # model="gpt-4-vision-preview",
        model="gpt-4-1106-preview",
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant answer questions, making observations, and being helpful to lab scientists. Your responses must be 2 to 3 sentences maximum. It is critical to be brief and to the point." },
            {
                "role": "user",
                "content": [
                    # { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" } }
                    { "type": "text", "text": question_text },
                ]
            }
        ],
        temperature=0.2,
    )
    # parse response
    response_text = response.choices[0].message.content
    print(f"[prompty_query] response: {response_text}")
    # return
    return response_text
