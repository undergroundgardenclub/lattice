from adafruit_debouncer import Debouncer
import digitalio
import json
import multiprocessing
import threading
import time
from utils_api import req_get_device_messages
from utils_device import calculate_offset_seconds, EVENT_TYPE_PLAY_AUDIO, EVENT_TYPE_RECORD_SERIES, EVENT_TYPE_RECORD_QUERY, led_main, led_pattern, PIN_RECORD_BUTTON
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
    "queue_messages": multiprocessing.Queue(),
    "queue_record_query": multiprocessing.Queue(),
    "queue_record_series": multiprocessing.Queue(),
    "queue_send_recording": multiprocessing.Queue(),
}
# --- events dict for passing to sub-processes
process_events = {
    # v1
    "event_recording_stop": multiprocessing.Event(),
    "event_recording_audio_stop": multiprocessing.Event(),
    "event_recording_video_stop": multiprocessing.Event(),
    # v2
    "event_is_recording_series": multiprocessing.Event(), # events start is_set() == False
    "event_is_recording_query": multiprocessing.Event(), # events start is_set() == False
}
# --- processes: recording
def processor_recorder_fork(pe, pq):
    import processor_recorder
    processor_recorder.processor_recorder(pe, pq)
ps_processor_recorder = multiprocessing.Process(target=processor_recorder_fork, args=(process_events, process_queues))
ps_processor_recorder.start()
# --- processes: sending (doing a thread to leave processors open for load balancing/orchestrating. this isn't doing dedicated work)
def processor_sender_fork(pe, pq):
    import processor_sender
    processor_sender.processor_sender(pe, pq)
ps_processor_sender = threading.Thread(target=processor_sender_fork, args=(process_events, process_queues))
ps_processor_sender.start()



# INTERACTION FNS
# --- single
def interaction_press_single(pe, pq):
    print('[interaction_press_single] triggered')
    led_pattern() # just for demoing/testing out. can't seem to trigger from other processes

# --- double
def interaction_press_double(pe, pq):
    print('[interaction_press_double] triggered')
    led_pattern("error")

# --- triple
def interaction_press_triple(pe, pq):
    print('[interaction_press_triple] triggered')
    if pe["event_is_recording_series"].is_set() == False: # start process if one doesn't exist
        now = time.time()
        pq['queue_record_series'].put({ "type": EVENT_TYPE_RECORD_SERIES, "data": { "media_id": generate_media_id(), "start_sec": now, "segment_start_sec": now } })
        pe["event_is_recording_series"].set()
    else:
        pe["event_is_recording_series"].clear()
        # TODO: trigger a job to summarize the series/session
        

# --- long press
def interaction_press_long(pe, pq, is_button_pressed):
    print('[interaction_press_long] triggered', is_button_pressed)
    if is_button_pressed == True and pe["event_is_recording_query"].is_set() == False:
        pq['queue_record_query'].put({ "type": EVENT_TYPE_RECORD_QUERY, "data": { "media_id": generate_media_id(), "start_sec": time.time() } })
        pe["event_is_recording_query"].set()
    elif is_button_pressed == False and pe["event_is_recording_query"].is_set() == True:
        pe["event_is_recording_query"].clear()


# PROCESS
# --- core 0 loop
print('[main] LOOP')
try:
    while True:
        now = time.time()
        # PERIPHERAL: SETUP
        button.update()
        is_button_pressed = not button.value


        # PERIPHERAL: LED (TODO: optimize so we're not constanly calling)
        if process_events["event_is_recording_series"].is_set() == True or process_events["event_is_recording_query"].is_set() == True:
            led_main.value = True
        else:
            led_main.value = False


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
            print(f"[device_message] processing: {next_message_type}", next_message_data)
            # ... execute
            if (next_message_type == EVENT_TYPE_PLAY_AUDIO):
                audio_bytes = get_file_bytes(next_message_data.get("file_url"))
                play_audio(audio_bytes, is_blocking=False)


        # PROCESS HEALTH CHECKS
        # --- ensure processors are still running (check if we can just start() or we need to redefine)
        if ps_processor_recorder.is_alive() == False:
            print("[loop] 'ps_processor_recorder' dead, starting again")
            ps_processor_recorder = multiprocessing.Process(target=processor_recorder_fork, args=(process_events, process_queues))
            ps_processor_recorder.start()
            led_pattern("error")
        if ps_processor_sender.is_alive() == False:
            print("[loop] 'ps_processor_sender' dead, starting again")
            ps_processor_sender = threading.Thread(target=processor_sender_fork, args=(process_events, process_queues))
            ps_processor_sender.start()
            led_pattern("error")


        time.sleep(0.01)  # Small delay to debounce and reduce CPU usage
except Exception as error:
    print("[loop] error: ", error)
    led_pattern("error")
