import json
import logging
import numpy as np
import pyaudio
import sys
import time
from env import env_recording_audio_channels, env_recording_audio_chunk_size, env_recording_frame_rate, env_recording_sample_rate
from utils_api import req_tracking_event
from utils_device import EVENT_TYPE_PLAY_AUDIO


# SETUP
# --- audio settings
audio_format = pyaudio.paInt16
audio_channels = env_recording_audio_channels()
audio_frame_rate = env_recording_frame_rate() # how do i get it to match!!?!!??
audio_sample_rate = env_recording_sample_rate() # 44100 is norm but trying to trim file sizes. also timing is better
audio_chunk = env_recording_audio_chunk_size()
# --- TODO: speech-to-text model


# PROCESSOR
def processor_listener(pe, pq):
    logging.info("[processor_listener] fork")
    # INIT
    audio = pyaudio.PyAudio()
    audio_frames = []
    # --- open stream
    audio_stream = audio.open(format=audio_format, channels=audio_channels, rate=audio_sample_rate, input=True, frames_per_buffer=audio_chunk)
    try:
        # LISTEN
        while audio_stream.is_active():
            try:
                audio_chunk_data = audio_stream.read(audio_chunk)
                # --- push to recorder if needed
                if pe["event_is_recording_query"].is_set() == True or pe["event_is_recording_series"].is_set() == True:
                    pq["queue_recorder_audio"].put(audio_chunk_data)
                # --- process for keyword/phrase actions
                audio_frames.append(audio_chunk_data)
                # try:
                #     logging.info("[processor_listener] Sphinx thinks you said %s", recognizer.recognize_sphinx(audio))
                # except Exception as sphinx_err:
                #     logging.info("[processor_listener] Sphinx thinks you said error: %s", sphinx_err)
                if len(audio_frames) > 200:
                    logging.info("[processor_listener] clearing frames")
                    audio_frames = []

            except Exception as proc_err:
                logging.error("[processor_listener] error: %s", proc_err)
                pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/an_error_has_occurred.mp3" }) })
                pq["queue_led"].put({ "type": "error" })
                req_tracking_event({ "type": "device_exception", "data": { "device_processor_name": "processor_listener", "error_message": proc_err } })

    except Exception as proc_camera_err:        
        logging.info('[processor_listener] error: %s', proc_camera_err)
        req_tracking_event({ "type": "device_exception", "data": { "device_processor_name": "processor_listener", "error_message": proc_camera_err } })
        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/an_error_has_occurred.mp3" }) })
        pq["queue_led"].put({ "type": "error" })
        pq["queue_led"].put({ "type": "off" })
        # sys.exit(1) # signal this was unexpected exiting

    # --- close stream if we hit err and are restarting
    audio_stream.stop_stream()
    audio_stream.close()
    audio.terminate()
