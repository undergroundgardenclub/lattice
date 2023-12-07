import digitalio
import multiprocessing
import os
import pygame
import sys
from env import env_device_id, env_directory_data, PIN_LED
from utils_data import get_file_bytes
from utils_media import combine_h264_and_wav_into_mp4, play_audio
from utils_network import send_api_query

# SETUP
# --- peripheral: LED for recording indicator
led_recording = digitalio.DigitalInOut(PIN_LED)
led_recording.direction = digitalio.Direction.OUTPUT
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
    media_path_video_h264 = f"{env_directory_data()}/{media_id}.h264"
    media_path_audio_wav = f"{env_directory_data()}/{media_id}.wav"
    media_path_final_mp4 = f"{env_directory_data()}/{media_id}.mp4"
    process_task_record_audio = multiprocessing.Process(target=process_task_record_audio_fork, args=(process_events, media_path_audio_wav))
    process_task_record_video = multiprocessing.Process(target=process_task_record_video_fork, args=(process_events, media_path_video_h264))
    # --- record
    process_task_record_audio.start()
    process_task_record_video.start()

    # AWAIT
    # --- led indicator
    led_recording.value = True
    # --- awaiting (aka blocking till resolves)
    process_task_record_audio.join()
    process_task_record_video.join()
    # --- combing video/audio
    combine_h264_and_wav_into_mp4(media_path_video_h264, media_path_audio_wav, media_path_final_mp4)
    # --- send API file payload
    query_response_data = send_api_query(media_path_final_mp4, dict(device_id=env_device_id()))
    # --- clean up src files
    os.remove(media_path_video_h264)
    os.remove(media_path_audio_wav)
    os.remove(media_path_final_mp4)

    # PLAY AUDIO
    # --- fetch audio (don't save to disk, keep in memory for simplicity, these are short and compress mp3s)
    audio_narration_file_url = query_response_data['file_url']
    audio_narration_response_bytes = get_file_bytes(audio_narration_file_url)
    # --- play
    play_audio(audio_narration_response_bytes)

    # EXIT
    # --- led indicator
    led_recording.value = False
    # --- process exit
    print('[process] task_query: exit')
    sys.exit(0)
