import digitalio
import multiprocessing
import os
import sys
import time
from uuid import uuid4
from env import env_device_id, env_directory_data
from utils_api import req_recording_batch_submit
from utils_device import led_main
from utils_files import delete_file, store_file_from_path, get_stored_file_url
from utils_media import calculate_offset_seconds, combine_h264_and_wav_into_mp4


# SETUP
# --- recording: audio
def process_task_record_audio_fork(pe, media_path_audio_wav):
    import task_record_audio
    task_record_audio.task_record_audio(pe, media_path_audio_wav)
# --- recording: video
def process_task_record_video_fork(pe, media_path_video_h264):
    import task_record_video
    task_record_video.task_record_video(pe, media_path_video_h264)
# --- media path for chunks
def get_media_key(media_id, media_chunk_num, media_format):
    return f"{media_id}--{media_chunk_num}.{media_format}"
def get_media_file_path(media_id, media_chunk_num, media_format):
    return f"{env_directory_data()}/{get_media_key(media_id, media_chunk_num, media_format)}"

# LOOP
def task_recording_series(process_events, media_id):
    print('[process] task_record_session: fork')

    # INIT
    # --- tell server we're starting a session? or is it that the first video, if a session id is present, that its associated
    device_id = env_device_id()
    session_id = uuid4()
    # --- led indicator
    led_main.value = True


    # RECORD
    chunk_count = 0
    chunk_duration_sec = 60 * 2 # random dropped frames throw video/audio out of sync. so keeping it short but there's a missing recording gap between segments
    chunk_start_ns = None # reset when each chunk is done?

    while process_events['event_recording_stop'].is_set() == False:
        chunk_count += 1
        chunk_start_ns = time.time_ns()
        # --- recording chunk: setup (TODO: should processing starts be done only once? and have video/audio processes responbile for chunking? that saves time for allocating processors)
        media_path_audio_wav = get_media_file_path(media_id, chunk_count, "wav")
        media_path_video_h264 = get_media_file_path(media_id, chunk_count, "h264")
        media_path_final_mp4 = get_media_file_path(media_id, chunk_count, "mp4")
        process_task_record_audio = multiprocessing.Process(target=process_task_record_audio_fork, args=(process_events, media_path_audio_wav))
        process_task_record_video = multiprocessing.Process(target=process_task_record_video_fork, args=(process_events, media_path_video_h264))
        # --- recording chunk: start
        process_task_record_audio.start()
        process_task_record_video.start()
        print('recording chunk: started')

        # --- block/sync until either event to stop or past chunk duration/length
        while process_events['event_recording_stop'].is_set() == False and calculate_offset_seconds(chunk_start_ns, time.time_ns()) < chunk_duration_sec:
            time.sleep(0.1) # easier on the CPU usage?
        
        # --- recording chunk: trigger video/audio end and wait for process to exit (may be duplicative, but harmless)
        print('recording chunk: set')
        process_events['event_recording_audio_stop'].set()
        process_events['event_recording_video_stop'].set()

        # --- recording chunk: await resolution
        print('recording chunk: join', process_events['event_recording_audio_stop'].is_set(), process_events['event_recording_video_stop'].is_set())
        process_task_record_audio.join()
        process_task_record_video.join()

        # --- recording chunk: merge
        # NOOP: taking time merging while not stopped will create breaks between segments

        # --- reset flags for video/audio
        process_events['event_recording_audio_stop'].clear()
        process_events['event_recording_video_stop'].clear()
        print('recording chunk: done')


    # PROCESS
    # --- encode mp4s + clean h264/wav files
    print('recording chunk: encoding')
    for i in range(chunk_count):        
        c = i + 1 # count/index starts at 1
        combine_h264_and_wav_into_mp4(
            get_media_file_path(media_id, c, "h264"),
            get_media_file_path(media_id, c, "wav"),
            get_media_file_path(media_id, c, "mp4"))
        delete_file(get_media_file_path(media_id, c, "h264"))
        delete_file(get_media_file_path(media_id, c, "h264.json"))
        delete_file(get_media_file_path(media_id, c, "wav"))
        delete_file(get_media_file_path(media_id, c, "wav.json"))
    # --- upload all to S3 + clean files mp4 files + compile list of files
    print('recording chunk: uploading')
    recording_files = []
    for i in range(chunk_count):
        c = i + 1
        mp4_key = get_media_key(media_id, c, "mp4")
        mp4_file_path = get_media_file_path(media_id, c, "mp4")
        store_file_from_path(mp4_file_path, mp4_key)
        delete_file(mp4_file_path)
        recording_files.append(dict(file_key=mp4_key, file_url=get_stored_file_url(mp4_key)))

    # --- send a req to backend for processing and creating an outline?
    print('recording chunk: sending api files list')
    req_recording_batch_submit(recording_files)
    

    # EXIT
    # --- led indicator
    led_main.value = False
    # --- process exit
    print('[process] task_record_session: exit')
    sys.exit(0)
