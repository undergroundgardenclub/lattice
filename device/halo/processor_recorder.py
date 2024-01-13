import json
import logging
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
import pyaudio
import sys
import time
import wave
from env import env_recording_frame_rate, env_recording_sample_rate
from utils_api import req_tracking_event
from utils_device import calculate_offset_seconds, EVENT_TYPE_PLAY_AUDIO, EVENT_TYPE_RECORD_SERIES, EVENT_TYPE_RECORD_QUERY, EVENT_TYPE_SEND_SERIES_RECORDING, EVENT_TYPE_SEND_QUERY_RECORDING
from utils_files import write_file_json
from utils_media import get_media_local_file_path, get_media_key


# SETUP
# --- video configs
video_frame_rate = env_recording_frame_rate()
video_frame_duration_limit = int(1_000_000 / video_frame_rate) # check manual for this recipocal calc
# video_size = (1280, 720) # determined now during runtime based on task (1600, 900) seems great, (1920, 1080) is big if recording long term, (1280, 720) seemed blurry with movement is a hinderance. err'ing to start on higher quality
video_encoder = H264Encoder(bitrate=10000000)
# --- audio configs
audio_format = pyaudio.paInt16
audio_channels = 1
audio_frame_rate = env_recording_frame_rate() # how do i get it to match!!?!!??
audio_sample_rate = env_recording_sample_rate() # 44100 is norm but trying to trim file sizes. also timing is better
audio_chunk = 1024
# --- meta traits
recording_segment_duration_sec = 60 * 2


# PROCESSOR
def processor_recorder(pe, pq): # process_events, process_queues
    logging.info('[processor_recorder] fork')
    # --- init (so we only have 1 instance of our camera)
    try:
        with Picamera2() as picam2: # seems this context manager is needed for camera availability errs/flow
            while True:
                try:
                    job_type = None
                    job_data = None
                    # --- query (prioritized if flagged)
                    if pe["event_is_recording_query"].is_set() == True:
                        if pq["queue_recorder_query"].qsize() > 0:
                            job = pq["queue_recorder_query"].get()
                            job_type = job["type"]
                            job_data = job.get("data")
                    # --- series
                    elif pe["event_is_recording_series"].is_set() == True:
                        if pq["queue_recorder_series"].qsize() > 0:
                            job = pq["queue_recorder_series"].get()
                            job_type = job["type"]
                            job_data = job.get("data")

                    # RECORD: CHECK
                    # --- if no job, skip
                    if job_type == None or job_data == None:
                        continue

                    # RECORD: VIDEO
                    logging.info("[processor_recorder] recording: %s %s", job_type, job_data)
                    # --- indicate recording
                    pq["queue_led"].put({ "type": "blink" })
                    pq["queue_led"].put({ "type": "on" })
                    # --- settings
                    media_id = job_data.get("media_id")
                    segment_start_sec = job_data.get("segment_start_sec", time.time())
                    file_key_mp4 = get_media_key(media_id, "mp4", int(segment_start_sec))
                    file_path_mp4 = get_media_local_file_path(media_id, "mp4", int(segment_start_sec)) # using int() to drop decimal
                    file_path_h264 = get_media_local_file_path(media_id, "h264", int(segment_start_sec))
                    file_path_wav = get_media_local_file_path(media_id, "wav", int(segment_start_sec))

                    # --- config tried having queries use higher settings, but think it's causing glitching
                    config_video_size = (1280, 720) # (1920, 1080) if job_type == EVENT_TYPE_RECORD_QUERY else (1280, 720)
                    config_video_quality = Quality.MEDIUM # Quality.VERY_HIGH if job_type == EVENT_TYPE_RECORD_QUERY else Quality.MEDIUM
                    logging.info("[processor_recorder] config quality/size: %s / %s", config_video_quality, config_video_size)
                    # --- config: init
                    picam2_config = picam2.create_video_configuration({ "size": config_video_size }, controls={ "FrameDurationLimits": (video_frame_duration_limit, video_frame_duration_limit) })
                    picam2.configure(picam2_config)
                    # --- record!... until...
                    picam2.start_recording(video_encoder, output=file_path_h264, quality=config_video_quality) # 2 min clips w/ LOW were ~14MB. Going to bump
                    video_start_time_sec = time.time()

                    # RECORD: AUDIO
                    audio = pyaudio.PyAudio()
                    audio_frames = []
                    # --- open stream
                    audio_stream = audio.open(format=audio_format, channels=audio_channels, rate=audio_sample_rate, input=True, frames_per_buffer=audio_chunk)
                    audio_start_time_sec = time.time()

                    # ... if query, wait until button is lifted (while we wait, push audio)
                    if job_type == EVENT_TYPE_RECORD_QUERY:
                        while pe["event_is_recording_query"].is_set() == True:
                            audio_chunk_data = audio_stream.read(audio_chunk)
                            audio_frames.append(audio_chunk_data)
                    # ... if segment, ensure recording flag is true, we're under 2 min, but interrupt if the query flag is flipped (while we wait, push audio)
                    elif job_type == EVENT_TYPE_RECORD_SERIES:
                        while pe["event_is_recording_series"].is_set() == True and pe["event_is_recording_query"].is_set() == False and calculate_offset_seconds(segment_start_sec, time.time()) < recording_segment_duration_sec:
                            audio_chunk_data = audio_stream.read(audio_chunk)
                            audio_frames.append(audio_chunk_data)

                    # RECORD: STOPPING
                    # --- resolve video recording
                    picam2.stop_recording()
                    # --- resolve video recording: save file/meta
                    write_file_json(file_path_h264 + '.json', { 'start_time_sec': video_start_time_sec })
                    # --- resolve audio recording
                    audio_stream.stop_stream()
                    audio_stream.close()
                    audio.terminate()
                    # --- resolve audio recording: save file/meta
                    with wave.open(file_path_wav, 'wb') as wf:
                        wf.setnchannels(audio_channels)
                        wf.setsampwidth(audio.get_sample_size(audio_format))
                        wf.setframerate(audio_sample_rate)
                        wf.writeframes(b''.join(audio_frames))
                    # --- create mp4 key/path for follow up
                    write_file_json(file_path_wav + '.json', { 'start_time_sec': audio_start_time_sec })


                    # FOLLOWUP ACTION
                    logging.info(f"[processor_recorder] following up")
                    # --- if this was a serial recording, and event says still recording, add next segment to queue (distinguished by segment_start_sec)
                    if job_type == EVENT_TYPE_RECORD_SERIES and pe["event_is_recording_series"].is_set() == True:
                        pq["queue_recorder_series"].put({ "type": EVENT_TYPE_RECORD_SERIES, "data": { **job_data, "segment_start_sec": time.time() } })
                        # --- beep so person knows recording is continuing
                        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/beep.mp3" }) })
                    # --- send to processor_recorder_send
                    if job_type == EVENT_TYPE_RECORD_SERIES:
                        pq["queue_sender"].put({ "type": EVENT_TYPE_SEND_SERIES_RECORDING, "data": { "file_path_h264": file_path_h264, "file_path_wav": file_path_wav, "file_path_mp4": file_path_mp4, "file_key_mp4": file_key_mp4, "series_id": job_data.get("series_id") } })
                    if job_type == EVENT_TYPE_RECORD_QUERY:
                        pq["queue_sender"].put({ "type": EVENT_TYPE_SEND_QUERY_RECORDING, "data": { "file_path_h264": file_path_h264, "file_path_wav": file_path_wav, "file_path_mp4": file_path_mp4, "file_key_mp4": file_key_mp4, "series_id": job_data.get("series_id") } })

                    # CLEAN
                    # --- reset job type/data to not rerun
                    job_type = None
                    job_data = None
                    # --- turn off light (it'll start again if we have a follow-up/queued recording ask, otherwise stays off if no follow up job)
                    pq["queue_led"].put({ "type": "off" })


                except Exception as proc_err:
                    logging.info('[processor_recorder] error: %s', proc_err)
                    req_tracking_event({ "type": "device_exception", "data": { "device_processor_name": "processor_recorder", "error_message": proc_err } })
                    pq["queue_led"].put({ "type": "error" })
                    pq["queue_led"].put({ "type": "off" })

                # --- slight pause to slow cpu cycles
                time.sleep(0.01)

    except Exception as proc_camera_err:
        logging.info('[processor_recorder] error: %s', proc_camera_err)
        req_tracking_event({ "type": "device_exception", "data": { "device_processor_name": "processor_recorder", "error_message": proc_camera_err } })
        pq["queue_messages"].put({ "type": EVENT_TYPE_PLAY_AUDIO, "data": json.dumps({ "file_path": "./media/an_error_has_occurred.mp3" }) })
        pq["queue_led"].put({ "type": "error" })
        pq["queue_led"].put({ "type": "off" })
        sys.exit(1) # attempting to trigger garbage clean up on this process and any references in case we hit a CmaFree allocation issue. main will restart proc
