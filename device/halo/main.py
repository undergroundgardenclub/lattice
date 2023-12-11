from adafruit_debouncer import Debouncer
import digitalio
import json
import multiprocessing
import time
from utils_api import req_get_device_messages
from utils_device import calculate_offset_seconds, led_pattern, PIN_RECORD_BUTTON
from utils_files import get_file_bytes
from utils_media import generate_media_id, play_audio


# SETUP
print('[main] SETUP')
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


# TASKS
# --- queues for data passing between processes
process_queues = {
    "queue_messages": multiprocessing.Queue()
}
# --- events dict for passing to sub-processes
process_events = {
    "event_recording_stop": multiprocessing.Event(),
    "event_recording_audio_stop": multiprocessing.Event(),
    "event_recording_video_stop": multiprocessing.Event(),
}
# --- recording
process_task_recording = None # if we have a process obj here, it's in motion
def process_task_recording_fork(pe, media_id):
    import task_recording # wrapper function so we only import in the new processor and don't have duplicate references
    task_recording.task_recording(pe, media_id)
# --- recording session
process_task_recording_series = None # if we have a process obj here, it's in motion
def process_task_recording_series_fork(pe, media_id):
    import task_recording_series # wrapper function so we only import in the new processor and don't have duplicate references
    task_recording_series.task_recording_series(pe, media_id)
# --- query
process_task_query = None # if we have a process obj here, it's in motion
def process_task_query_fork(pe, media_id):
    import task_query # wrapper function so we only import in the new processor and don't have duplicate references
    task_query.task_query(pe, media_id)


# INTERACTION FNS
# --- single
def interaction_press_single():
    print('[interaction_press_single] triggered')
    led_pattern() # just for demoing/testing out. can't seem to trigger from other processes

# --- double
def interaction_press_double():
    print('[interaction_press_double] triggered')
    led_pattern("error")

# --- triple
def interaction_press_triple():
    print('[interaction_press_triple] triggered')
    global process_task_recording_series # means we can reach outside our functions scope
    print(f'[interaction_press_double] recording: {"started" if process_task_recording_series == None else "stopping"}')
    if process_task_recording_series == None: # start process if one doesn't exist
        media_id = generate_media_id()
        process_task_recording_series = multiprocessing.Process(target=process_task_recording_series_fork, args=(process_events, media_id))
        process_task_recording_series.start()
    else:
        process_events['event_recording_stop'].set() # trigger stop event
        process_task_recording_series.join() # TODO: instead of join() we need to iteratively check up on this so we don't block other interactions
        process_events['event_recording_stop'].clear() # clear process reference. and "unset" which we are using for control flow (maybe start should be this way too rather than None)
        process_task_recording_series = None

# --- long press
def interaction_press_long(is_button_pressed):
    print('[interaction_press_long] triggered', is_button_pressed)
    global process_task_query
    print(f'[interaction_press_double] query: {"started" if process_task_query == None else "stopping"}')
    if is_button_pressed == True:
        media_id = generate_media_id()
        process_task_query = multiprocessing.Process(target=process_task_query_fork, args=(process_events, media_id))
        process_task_query.start()
    else:
        process_events['event_recording_stop'].set()
        process_task_query.join()  # TODO: instead of join() we need to iteratively check up on this so we don't block other interactions
        process_events['event_recording_stop'].clear()
        process_task_query = None


# LOOP
print('[main] LOOP')
try:
    while True:
        now = time.monotonic()
        # --- peripheral: button
        button.update()
        is_button_pressed = not button.value


        # PERIPHERAL INTERACTION PATTERN
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
            interaction_press_single()
            interaction_active = None

        elif interaction_active == "press_double":
            interaction_press_double()
            interaction_active = None

        elif interaction_active == "press_triple":
            interaction_press_triple()
            interaction_active = None

        elif interaction_active == "press_long_start" and is_button_pressed:
            interaction_press_long(is_button_pressed)
            interaction_active = "press_long_in_flight" # set new state so we don't continuously run this. the other will end

        elif interaction_active == "press_long_in_flight" and is_button_pressed == False:
            interaction_press_long(is_button_pressed)
            interaction_active = None


        # MESSAGES LISTENING
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
            print(f"[device_message] processing: {next_message_type}", next_message_data)
            # ... execute
            if (next_message_type == "play_audio"):
                audio_bytes = get_file_bytes(next_message_data.get("file_url"))
                play_audio(audio_bytes, is_blocking=False)


        time.sleep(0.1)  # Small delay to debounce and reduce CPU usage
except Exception as error:
    print("[loop] error: ", error)
    led_pattern("error")
