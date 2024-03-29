import board
import digitalio
import logging
import time
from typing import Optional


# PINS (https://www.electrorules.com/raspberry-pi-4-gpio-pnout/)
PIN_RECORD_BUTTON = board.D14
PIN_LED = board.D23


# EVENT ENUMS
EVENT_TYPE_PLAY_AUDIO = "play_audio"
EVENT_TYPE_RECORD_SERIES = "record_series"
EVENT_TYPE_RECORD_QUERY = "record_query"
EVENT_TYPE_SEND_SERIES_RECORDING = "send_series_recording"
EVENT_TYPE_SEND_SERIES_DONE = "send_series_done"
EVENT_TYPE_SEND_QUERY_RECORDING = "send_query_recording"


# IDs
def get_device_identifier():
  """
  Get a unique identifier for the device from CPU serial
  """
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000" 
  return cpuserial
  

# PERIPHERALS
led_main = digitalio.DigitalInOut(PIN_LED)
led_main.direction = digitalio.Direction.OUTPUT

def led_pattern(pattern_type: str = None):
    logging.info("[led_pattern] %s", pattern_type)
    # --- get current state (ex: if its on for a recording)
    current_led_state = led_main.value
    # --- set pattern
    num_blinks = 1
    delay_blinks = 0.1
    if pattern_type == "blink":
        num_blinks = 1
        delay_blinks = 0.1
    elif pattern_type == "error":
        num_blinks = 5
        delay_blinks = 0.1

    # --- execute pattern
    for i in range(num_blinks):
        led_main.value = True
        time.sleep(delay_blinks)
        led_main.value = False
        time.sleep(delay_blinks)

    # --- return to prior state
    led_main.value = current_led_state


# TIMERS
def calculate_offset_seconds(earlier_sec, later_sec_at):
    offset = later_sec_at - earlier_sec
    # logging.info(f"[calculate_offset_seconds] {later_sec_at} - {earlier_sec} = {offset}") # processes run this alot so hiding
    return offset
