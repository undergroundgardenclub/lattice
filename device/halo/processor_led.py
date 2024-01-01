import json
import logging
import time
from utils_api import req_tracking_event
from utils_device import led_main, led_pattern


# PROCESSOR
def processor_led(pe, pq):
    logging.info('[processor_led] fork')
    while True:
        try:
            # GET
            job_type = None # aka LED pattern
            # --- check for jobs
            if pq["queue_led"].qsize() > 0:
                job = pq["queue_led"].get()
                job_type = job["type"]
            
            # TRIGGER
            if job_type != None:
              # --- values
              if job_type == "on":
                led_main.value = True
              elif job_type == "off":
                led_main.value = False
              # --- patterns
              elif job_type == "error":
                led_pattern("error")
              elif job_type == "blink":
                led_pattern("blink")
              

        except Exception as proc_err:
            logging.error('[processor_led] error: %s', proc_err)
            pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/an_error_has_occurred.mp3" }) })
            pq["queue_led"].put({ "type": "error" })
            req_tracking_event({ "type": "device_exception", "data": { "device_processor_name": "processor_led", "error_message": proc_err } })

        # -- continue
        time.sleep(0.1)
