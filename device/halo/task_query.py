import digitalio
import multiprocessing
import os
import pygame
import sys
from env import env_device_id, env_directory_data
from utils_api import req_query
from utils_files import delete_file, get_file_bytes, get_stored_file_url, store_file_from_path
from utils_device import led_main
from utils_media import combine_h264_and_wav_into_mp4, get_media_local_file_path, get_media_key, play_audio

# SETUP
# --- recording: audio
def process_task_record_audio_fork(pe, media_path_audio_wav):
    import task_record_audio
    task_record_audio.task_record_audio(pe, media_path_audio_wav)
# --- recording: video
def process_task_record_video_fork(pe, media_path_video_h264):
    import task_record_video
    task_record_video.task_record_video(pe, media_path_video_h264)


# LOOP
def task_query(process_events, media_id):
    print('[process] task_query: fork')
    # START
    # --- prep processors
    media_path_video_h264 = get_media_local_file_path(media_id, "h264")
    media_path_audio_wav = get_media_local_file_path(media_id, "wav")
    media_path_final_mp4 = get_media_local_file_path(media_id, "mp4")
    media_mp4_key = get_media_key(media_id, "mp4")
    process_task_record_audio = multiprocessing.Process(target=process_task_record_audio_fork, args=(process_events, media_path_audio_wav))
    process_task_record_video = multiprocessing.Process(target=process_task_record_video_fork, args=(process_events, media_path_video_h264))
    # --- record
    process_task_record_audio.start()
    process_task_record_video.start()

    # AWAIT
    # --- led indicator
    led_main.value = True
    # --- awaiting (aka blocking till resolves)
    process_task_record_audio.join()
    process_task_record_video.join()

    # PROCESS
    # --- encode mp4s + clean h264/wav files
    combine_h264_and_wav_into_mp4(media_path_video_h264, media_path_audio_wav, media_path_final_mp4)
    # --- upload query recording to S3
    store_file_from_path(media_path_final_mp4, media_mp4_key)
    # --- clean up files
    delete_file(media_path_video_h264)
    delete_file(media_path_video_h264 + ".json")
    delete_file(media_path_audio_wav)
    delete_file(media_path_audio_wav + ".json")
    delete_file(media_path_final_mp4)
    # --- send API req
    query_response_data = req_query(query_file=dict(file_key=media_mp4_key, file_url=get_stored_file_url(media_mp4_key)))

    # PLAY AUDIO
    # --- fetch audio (don't save to disk, keep in memory for simplicity, these are short and compress mp3s)
    audio_narration_file_url = query_response_data['file_url']
    audio_narration_response_bytes = get_file_bytes(audio_narration_file_url)
    # --- play
    play_audio(audio_narration_response_bytes)

    # EXIT
    # --- led indicator
    led_main.value = False
    # --- process exit
    print('[process] task_query: exit')
    sys.exit(0)
