import json
import numpy as np
import yaml
from types import SimpleNamespace
from typing import List
from openai import OpenAI
from env import env_open_ai_api_key
from vision.cv import encoded_frame_to_base64


openai_client = OpenAI(api_key=env_open_ai_api_key())


# QUERY
# --- tool/action requests
class QueryTools:
    def __init__(self):
        self.tools = {
            "send_recording_series_summary_email": {
                "name": "send_recording_series_summary_email",
                "description": "Get an email sent to you about recordings you've done today or yesterday.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "interval_unit": { "type": "string", "enum": ["days"], "default": "days" },
                        "interval_num": { "type": "integer", "default": 0 },
                    },
                }
            },
            "send_video_series_slice": {
                "name": "send_video_series_slice",
                "description": "Get a recording that covers some number of minutes or hours.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "interval_unit": { "type": "string", "enum": ["minutes", "hours"], "default": "minutes" },
                        "interval_num": { "type": "integer", "default": 15 },
                    },
                }
            },
            "question_answer": {
                "name": "question_answer",
                "description": "Get answers to general questions, excluding device settings and functionality.",
                "schema": { "type": "object", "properties": {} }
            },
            "help_manual_about_tool": {
                "name": "help_manual_about_tool",
                "description": "Learn about this device's functionality and what spoken commands it accepts.",
                "schema": { "type": "object", "properties": {} }
            },
            "other": {
                "name": "other",
                "description": "Catch all category for unclear intents",
                "schema": { "type": "object", "properties": {} }
            },
        }
    def get_tools_names(self):
        return list(self.tools.keys())

# --- query action decision making enum
def prompt_query_action(input_text: str):
    print(f"[prompt_query_action] querying")
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": f"You are a helpful assistant trying to understand which function to run from a user request. You are only allowed to use the following functions: {json.dumps(QueryTools().tools)}. Respond in the JSON format, {{ 'functionName': str, 'functionArgs': dict }}." },
            { "role": "user", "content": input_text }
        ],
        temperature=0.2,
        max_tokens=400,
    )
    # parse response
    data = json.loads(response.choices[0].message.content)
    function_name = data['functionName']
    function_args = data['functionArgs']
    print(f"[prompty_query] response: {function_name}", function_args)
    # return
    return function_name, function_args

# --- help manual
def prompt_query_help_manual():
    print(f"[prompt_query_help_manual] querying")
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            { "role": "system", "content": f"You are a helpful assistant telling a user what voice-based commands they can use with this device. Briefly describe the functionality and their params. Exclude tools themed as 'other' or 'miscellaneous' or 'help manual'." },
            { "role": "user", "content": f"Narrate a description of the commands a person can use: {json.dumps(QueryTools().tools)}" },
        ],
        temperature=0.2,
        max_tokens=400,
    )
    # parse response
    response_text = response.choices[0].message.content
    print(f"[prompty_query] response: ", response_text)
    # return
    return response_text


# TRANSCRIPTS
# --- header/steps
def prompt_recording_transcript_to_task_headers(input_text_transcript: str) -> List[str]:
    # query
    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant designed to output JSON of a protocol with the schema, { protocolTaskHeaders: string[] }. Given an audio transcript, list out the headlines for this protocol. Details are not for this step. Example) { protocolTaskHeaders: ['Gather Reagents', 'Heat Shock Plasmids into E.Coli', 'Plate Cells', 'Incubate Cells'] }" },
            { "role": "user", "content": input_text_transcript }
        ],
        temperature=0.2,
    )
    # parse response
    data = json.loads(response.choices[0].message.content)
    headers = data['protocolTaskHeaders']
    print(f"[prompt_recording_transcript_to_task_headers] headers: {headers}")
    # return
    return headers

# --- outline (from header/steps)
def prompt_recording_transcript_to_task_outline(transcripts_sentences: str, task_headers: List[str]):
    # query
    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        # model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant designed to output JSON representing a transcript of work being done with this schema, { protocolTasks: { taskName: str; taskSummary: str; taskActions: str[]; taskStartAtSecond?: int; taskEndAtSecond?: int; }[] }. Given an audio transcript as YML and a list of task names, derive summaries of what occurred with each task and list a related set of actions and their details if mentioned." },
            # converting to YML because its considered fewer tokens
            { "role": "user", "content": f"Task Names: {task_headers}\n\nTranscript YML:\n\n{yaml.dump(transcripts_sentences)}" }
        ],
        temperature=0.2,
    )
    # parse response
    data = json.loads(response.choices[0].message.content)
    tasks = data['protocolTasks']
    print(f"[prompt_recording_transcript_to_task_headers] tasks: ", tasks)
    print(f"[prompt_recording_transcript_to_task_headers] num tasks: {len(tasks)}")
    # return
    return tasks


# QUESTION ANSWERING
# --- data requests
def prompt_query_general_question_answer(input_text: str, question_image_arr: np.ndarray):
    print(f"[prompt_query_general_question_answer] querying")
    # encode image
    base64_image = encoded_frame_to_base64(question_image_arr)
    # query
    response = openai_client.chat.completions.create(
        # model="gpt-4-vision-preview", # I'd like faster queries on data, and visuals is less important for that
        model="gpt-4-1106-preview",
        messages=[
            { "role": "system", "content": "You are a helpful lab assistant answer questions, making observations, and being helpful to lab scientists. Your responses must be 2 to 3 sentences maximum. It is critical to be brief and to the point." },
            {
                "role": "user",
                "content": [
                    # { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" } },
                    { "type": "text", "text": input_text },
                ]
            }
        ],
        temperature=0.2,
        max_tokens=400,
    )
    # parse response
    response_text = response.choices[0].message.content
    print(f"[prompty_query] response: {response_text}")
    # return
    return response_text


