import pygame
import subprocess
import time
from env import env_device_id, env_recording_frame_rate, env_recording_sample_rate

def convert_h264_to_mp4(input_file: str, output_file: str, frame_rate: int):
    command = ["ffmpeg", "-r", str(frame_rate), "-i", input_file, "-c:v", "copy", "-c:a", "copy", output_file]
    subprocess.run(command)

def combine_h264_and_wav_into_mp4(video_file_path, audio_file_path, output_file_path):
    command = [
        "ffmpeg",
        "-r", str(env_recording_frame_rate()), # video capture frame rate
        "-i", video_file_path,
        '-itsoffset', str(-1), # offsetting audio by 1 second to line up w/ video. looks good!
        "-i", audio_file_path,
        "-c:v", "copy", # copy the video stream
        "-channel_layout", "mono",
        "-c:a", "aac", # re-encode the audio to AAC
        "-strict", "experimental",
        "-ar", str(env_recording_sample_rate()),
        '-map', '0:v:0', # for offset, don't apply change to video
        '-map', '1:a:0', # for offset, apply change to audio
        output_file_path
    ]
    subprocess.run(command, check=True)

def generate_media_id():
    return f"{env_device_id()}-{int(time.time())}"

def play_audio(audio_bytes):
    print("[play_audio] playing audio!")
    pygame.mixer.init()
    pygame.mixer.music.load(audio_bytes)
    # optionally, we can check if there is something already playing
    pygame.mixer.music.play()