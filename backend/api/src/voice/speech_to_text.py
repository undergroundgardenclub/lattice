import math
from typing import Optional
import pydash as _
import requests
from time import sleep
from env import env_get_assembly_ai_api_key

# HACK: just carrying this over from gideon
TOKENIZING_STRING_SENTENCE_SPLIT_MIN_LENGTH = 80


def speech_to_text(file_url: Optional[str] = None, transcript_id: Optional[str] = None) -> { "text": str, "sentences": list({ "text": str, "second_start": int, "second_stop": int }), "words": list({ "text": str, "start": int, "end": int }) }:
    # REQUEST
    # if provided a transcript_id, we will use that for our data fetch, rather than re-transcribe
    t_id = transcript_id
    if transcript_id == None:
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={ "authorization": env_get_assembly_ai_api_key(), "content-type": "application/json" },
            json={ "audio_url": file_url }
        )
        print("[speech_to_text] transcript requested", transcript_response.json()['id'], transcript_response.json()['status'])
        t_id = transcript_response.json()['id']
    is_transcript_complete = False
    transcript_response = None

    # POLL FOR RESULTS
    while is_transcript_complete == False:
        transcript_check_response = requests.get(
            "https://api.assemblyai.com/v2/transcript/{t_id}".format(t_id=t_id),
            headers={ "authorization": env_get_assembly_ai_api_key() },
        )
        print(f"[speech_to_text] transcript {t_id} status: '{transcript_check_response.json()['status']}'")
        if transcript_check_response.json()['status'] == 'completed':
            is_transcript_complete = True
            transcript_response = transcript_check_response.json()
        if transcript_check_response.json()['status'] == 'error':
            print("[speech_to_text] error", transcript_check_response.json())
            raise transcript_check_response.json()
        sleep(3)
        
    # PROCESS (crude words -> sentences + full text construction)
    print(f"[speech_to_text] processing {t_id}") # transcript_response
    # --- sentences
    sentences = []
    sentence_milliseconds_start = None
    sentence_milliseconds_end = None
    sentence_text_fragments = []
    for word in transcript_response['words']:
        if (sentence_milliseconds_start == None): sentence_milliseconds_start = word['start']
        sentence_milliseconds_end = word['end']
        sentence_text_fragments.append(word['text'])
        # print("[speech_to_text] word", word)
        # --- if contains a period and word length is significant
        if (_.has_substr(word['text'], ".") and len(word['text']) > 3 and len(" ".join(sentence_text_fragments)) > TOKENIZING_STRING_SENTENCE_SPLIT_MIN_LENGTH):
            sentence = {
                "text": " ".join(sentence_text_fragments),
                "second_start": math.floor(sentence_milliseconds_start / 1000),
                "second_end": math.floor(sentence_milliseconds_end / 1000),
            }
            # print("[speech_to_text] sentence", sentence)
            sentences.append(sentence)
            sentence_text_fragments = []
            sentence_milliseconds_start = None
            sentence_milliseconds_end = None

    # RETURN
    results = {
        'response': transcript_response, # if we want to do other operations
        'sentences': sentences,
        'text': transcript_response['text'],
        'words': transcript_response['words'],
    }
    print(f"[speech_to_text] transcribed {t_id}")
    return results
