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
record_button_input = digitalio.DigitalInOut(PIN_RECORD_BUTTON)
record_button_input.switch_to_input(pull=digitalio.Pull.UP) # if button pressed, button.fell = True
record_button = Debouncer(record_button_input)
# --- recording
process_task_record = None # if we have a process obj here, it's in motion
def process_task_record_fork(pe, media_id):
    import task_record
    task_record.task_record(pe, media_id)
# --- events dict for passing to sub-processes
process_events = {
    'event_stop_recording': multiprocessing.Event()
}


# LOOP
print('[main] LOOP')
try:
    while True:
        # SENSORY UPDATES
        record_button.update()

        # ACT
        # --- recording
        if record_button.fell == True:
            # ... if not recording, set bool = True so we don't re-trigger
            if process_task_record == None:
                print('[loop] Recording: Started')
                # start process
                media_id = f"{env_device_id()}-{int(time.time())}"
                process_task_record = multiprocessing.Process(target=process_task_record_fork, args=(process_events, media_id))
                process_task_record.start()
            else:
                print('[loop] Recording: Stopping...')
                # trigger stop event
                process_events['event_stop_recording'].set()
                # wait for process to resolve
                process_task_record.join()
                # clear process reference. and "unset" which we are using for control flow (maybe start should be this way too rather than None)
                process_events['event_stop_recording'].clear()
                process_task_record = None
                print('[loop] Recording: Stopped')
except Exception as error:
    print("[loop] error: ", error)
