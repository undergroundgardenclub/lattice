from adafruit_debouncer import Debouncer
import board
import digitalio
import multiprocessing
import time
from env import env_device_id, PIN_RECORD_BUTTON
from task_record import task_record 


# SETUP
print('[main] SETUP')
# --- peripherals (maybe should be global references for control overrides by subprocesses?)
button_input = digitalio.DigitalInOut(PIN_RECORD_BUTTON)
button_input.switch_to_input(pull=digitalio.Pull.UP) # if button pressed, button.fell = True
button = Debouncer(button_input)
# --- interaction trackers/globals
BUTTON_PRESS_TIMER = 1.0 # seconds
button_press_count = 0
button_press_last_at = 0
button_press_last_state = False
interaction_active = None


# TASKS
# --- events dict for passing to sub-processes
process_events = {
    'event_stop_recording': multiprocessing.Event()
}


# INTERACTION FNS
# --- single
def interaction_press_single():
    print('[interaction_press_single] triggered')

# --- double (recording)
process_task_record = None # if we have a process obj here, it's in motion
def process_task_record_fork(pe, media_id):
    import task_record # wrapper function so we only import in the new processor and don't have duplicate references
    task_record.task_record(pe, media_id)

def interaction_press_double():
    print('[interaction_press_double] triggered')
    global process_task_record # means we can reach outside our functions scope
    print(f'[interaction_press_double] recording: {"started" if process_task_record == None else "stopping"}')
    if process_task_record == None:
        # start process if one doesn't exist
        media_id = f"{env_device_id()}-{int(time.time())}"
        process_task_record = multiprocessing.Process(target=process_task_record_fork, args=(process_events, media_id))
        process_task_record.start()
    else:
        # trigger stop event
        process_events['event_stop_recording'].set()
        # wait for process to resolve
        process_task_record.join()
        # clear process reference. and "unset" which we are using for control flow (maybe start should be this way too rather than None)
        process_events['event_stop_recording'].clear()
        process_task_record = None
        print('[interaction_press_double] recording: stopped')

# --- long press
def interaction_press_long(is_button_pressed):
    print('[interaction_press_long] triggered', is_button_pressed)
    return


# LOOP
print('[main] LOOP')
try:
    while True:
        now = time.monotonic()
        # --- peripheral: button
        button.update()
        is_button_pressed = not button.value


        # INTERACTION PATTERN
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
        if now - button_press_last_at >= BUTTON_PRESS_TIMER:
            # ... if still held down, we're long
            if button_press_count == 1 and is_button_pressed:
                interaction_active = "press_long_start"
            # ... if not held down, we're short
            elif button_press_count == 1 and is_button_pressed == False:
                interaction_active = "press_single"
            # ... if two presses and not held down, we're double
            elif button_press_count == 2:
                interaction_active = "press_double"
            # ... reset
            button_press_count = 0

        # --- run interaction
        if interaction_active == "press_single":
            interaction_press_single()
            interaction_active = None

        elif interaction_active == "press_double":
            interaction_press_double()
            interaction_active = None

        elif interaction_active == "press_long_start" and is_button_pressed:
            interaction_press_long(is_button_pressed)
            interaction_active = "press_long_in_flight" # set new state so we don't continuously run this. the other will end

        elif interaction_active == "press_long_in_flight" and is_button_pressed == False:
            interaction_press_long(is_button_pressed)
            interaction_active = None


        time.sleep(0.01)  # Small delay to debounce and reduce CPU usage
except Exception as error:
    print("[loop] error: ", error)
