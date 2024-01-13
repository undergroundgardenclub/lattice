from adafruit_debouncer import Debouncer
import digitalio
import json
import logging
import multiprocessing
import os
import threading
import time
from uuid import uuid4
from env import env_device_id, env_directory_logs
from utils_api import req_get_device_messages, req_tracking_event
from utils_device import calculate_offset_seconds, EVENT_TYPE_PLAY_AUDIO, EVENT_TYPE_RECORD_SERIES, EVENT_TYPE_SEND_SERIES_DONE, EVENT_TYPE_RECORD_QUERY, led_main, PIN_RECORD_BUTTON
from utils_files import get_file_bytes
from utils_media import generate_media_id, play_audio


# SETUP
# --- logging file
logging.basicConfig(filename=env_directory_logs() + "halo.log", level=logging.DEBUG)
logging.info('[main] SETUP')
# --- peripherals (maybe should be global references for control overrides by subprocesses?)
button_input = digitalio.DigitalInOut(PIN_RECORD_BUTTON)
button_input.switch_to_input(pull=digitalio.Pull.UP) # if button pressed, button.fell = True
button = Debouncer(button_input)
# --- interaction trackers/globals
BUTTON_PRESS_WINDOW_TIME_SECS = 1.2 # seconds
button_press_count = 0
button_press_last_at = 0 # int for less conditional logic
button_press_last_state = False
interaction_active = None
# --- message listener
DEVICE_MESSAGES_CHECK_WINDOW_TIME_SECS = 5
device_messages_checked_last_at = 0 # int for less conditional logic
# --- recording session helpers
series_id = None # set/clear when triple tapping. going to set to a random uuid


# TASKS
# --- queues for data passing between processes
process_queues = {
    "queue_led": multiprocessing.Queue(),
    "queue_messages": multiprocessing.Queue(),
    "queue_recorder_query": multiprocessing.Queue(),
    "queue_recorder_series": multiprocessing.Queue(),
    "queue_sender": multiprocessing.Queue(),
}
# --- events dict for passing to sub-processes
process_events = {
    "event_is_recording_series": multiprocessing.Event(), # events start is_set() == False
    "event_is_recording_query": multiprocessing.Event(), # events start is_set() == False
}
# --- processor: recording
def processor_recorder_fork(pe, pq):
    import processor_recorder
    processor_recorder.processor_recorder(pe, pq)
ps_processor_recorder = multiprocessing.Process(target=processor_recorder_fork, args=(process_events, process_queues))
# --- processor: sending (doing a thread to leave processors open for load balancing/orchestrating. this isn't doing dedicated work)
def processor_sender_fork(pe, pq):
    import processor_sender
    processor_sender.processor_sender(pe, pq)
ps_processor_sender = threading.Thread(target=processor_sender_fork, args=(process_events, process_queues))
# --- processor: led patterns (this can be blocking, so offloading this to unblock main loop)
def processor_led_fork(pe, pq):
    import processor_led
    processor_led.processor_led(pe, pq)
ps_processor_led = threading.Thread(target=processor_led_fork, args=(process_events, process_queues))


# INTERACTION FNS
# --- single
def interaction_press_single(pe, pq):
    logging.info('[interaction_press_single] triggered')
    pq["queue_led"].put({ "type": "blink" }) # just for demoing/testing out. can't seem to trigger from other processes
    pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/beep.mp3" }) })

# --- double
def interaction_press_double(pe, pq):
    logging.info('[interaction_press_double] triggered')
    pq["queue_led"].put({ "type": "error" })
    pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/chime.mp3" }) })

# --- triple
def interaction_press_triple(pe, pq):
    logging.info('[interaction_press_triple] triggered')
    global series_id
    if pe["event_is_recording_series"].is_set() == False: # start process if one doesn't exist
        series_id = str(uuid4())
        now = time.time()
        pq['queue_recorder_series'].put({ "type": EVENT_TYPE_RECORD_SERIES, "data": { "media_id": generate_media_id(), "series_id": series_id, "start_sec": now, "segment_start_sec": now } })
        pe["event_is_recording_series"].set()
        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/recording_started.mp3" }) })
    else:
        pe["event_is_recording_series"].clear()
        pq['queue_sender'].put({ "type": EVENT_TYPE_SEND_SERIES_DONE, "data": { "series_id": series_id } })
        series_id = None
        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/recording_stopped.mp3" }) })

# --- long press
def interaction_press_long(pe, pq, is_button_pressed):
    logging.info('[interaction_press_long] triggered: %s', is_button_pressed)
    global series_id
    if is_button_pressed == True and pe["event_is_recording_query"].is_set() == False:
        pq['queue_recorder_query'].put({ "type": EVENT_TYPE_RECORD_QUERY, "data": { "media_id": generate_media_id(), "series_id": series_id, "start_sec": time.time() } })
        pe["event_is_recording_query"].set()
        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/yes.mp3" }) })
    elif is_button_pressed == False and pe["event_is_recording_query"].is_set() == True:
        pe["event_is_recording_query"].clear()
        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/working_on_it.mp3" }) })


# PROCESSOR/LOOP
logging.info('[main] LOOP')
# --- blink to signal we've starting
process_queues["queue_led"].put({ "type": "blink" })
# --- save event about boot up
req_tracking_event({ "type": "device_boot", "data": {} })
# --- loop
while True:
    try:
        now = time.time()
        # PERIPHERAL: SETUP
        button.update()
        is_button_pressed = not button.value

        # PERIPHERAL: BUTTON
        # --- listen for clicks
        if is_button_pressed and button_press_last_state == False:
            button_press_last_state = True
            # set initial click timer if this is first click
            if button_press_count == 0:
                button_press_last_at = now
            button_press_count += 1
        elif button.value and button_press_last_state == True:
            button_press_last_state = False

        # --- if we're 1 second past, initial click, determine which interaction we're having
        if now - button_press_last_at >= BUTTON_PRESS_WINDOW_TIME_SECS:
            # ... if still held down, we're long
            if button_press_count == 1 and is_button_pressed:
                interaction_active = "press_long_start"
            # ... if not held down, we're short
            elif button_press_count == 1 and is_button_pressed == False:
                interaction_active = "press_single"
            # ... if two presses and not held down, we're double
            elif button_press_count == 2:
                interaction_active = "press_double"
            elif button_press_count == 3:
                interaction_active = "press_triple"
            # ... reset
            button_press_count = 0

        # --- run interaction (continues from state change above)
        if interaction_active == "press_single":
            interaction_press_single(process_events, process_queues)
            interaction_active = None
        elif interaction_active == "press_double":
            interaction_press_double(process_events, process_queues)
            interaction_active = None
        elif interaction_active == "press_triple":
            interaction_press_triple(process_events, process_queues)
            interaction_active = None
        elif interaction_active == "press_long_start" and is_button_pressed:
            interaction_press_long(process_events, process_queues, is_button_pressed)
            interaction_active = "press_long_in_flight" # set new state so we don't continuously run this. the other will end
        elif interaction_active == "press_long_in_flight" and is_button_pressed == False:
            interaction_press_long(process_events, process_queues, is_button_pressed)
            interaction_active = None


        # MESSAGES LISTENING (TODO: move into a thread? prob unnecessary resource allocation)
        # --- fetch messages if any exist, add to queue
        if now - device_messages_checked_last_at >= DEVICE_MESSAGES_CHECK_WINDOW_TIME_SECS:
            device_messages_checked_last_at = now
            new_messages = req_get_device_messages()
            if len(new_messages) > 0:
                for m in new_messages:
                    process_queues["queue_messages"].put(m)

        # --- if messages queued, do it (will become multi-thread/processor oriented)
        if process_queues["queue_messages"].qsize() > 0:
            # ... parse data from json string
            next_message = process_queues["queue_messages"].get()
            next_message_type = next_message["type"]
            next_message_data = json.loads(next_message.get("data"))
            logging.info("[device_message] processing: %s %s", next_message_type, next_message_data)
            # ... execute
            if (next_message_type == EVENT_TYPE_PLAY_AUDIO):
                audio_bytes = get_file_bytes(next_message_data.get("file_path") or next_message_data.get("file_url")) # local files for audio cues of actions
                play_audio(audio_bytes, is_blocking=False)


        # PROCESS HEALTH CHECKS
        # --- ensure processors are still running (check if we can just start() or we need to redefine)
        if ps_processor_recorder.is_alive() == False:
            logging.info("[loop] 'ps_processor_recorder' is_alive = %s, starting again", ps_processor_recorder.is_alive())
            ps_processor_recorder = multiprocessing.Process(target=processor_recorder_fork, args=(process_events, process_queues))
            ps_processor_recorder.start()
            ps_processor_recorder.is_alive()
            logging.info("[loop] 'ps_processor_recorder' is_alive = %s, starting again", ps_processor_recorder.is_alive())
        if ps_processor_sender.is_alive() == False:
            logging.info("[loop] 'ps_processor_sender' is_alive = %s, starting again", ps_processor_sender.is_alive())
            ps_processor_sender = threading.Thread(target=processor_sender_fork, args=(process_events, process_queues))
            ps_processor_sender.start()
        if ps_processor_led.is_alive() == False:
            logging.info("[loop] 'ps_processor_led' is_alive = %s, starting again", ps_processor_led.is_alive())
            ps_processor_led = threading.Thread(target=processor_led_fork, args=(process_events, process_queues))
            ps_processor_led.start()


    except Exception as main_err:
        logging.error("[loop] error: %s", main_err)
        process_queues["queue_led"].put({ "type": "error" })
        process_queues["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/an_error_has_occurred.mp3" }) })
        req_tracking_event({ "type": "device_exception", "data": { "device_processor_name": "main", "error_message": main_err } })

    time.sleep(0.01)  # if we slow delay, button interactivity becomes wonky, keep at 0.01
