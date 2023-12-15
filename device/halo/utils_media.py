import logging
from pygame import mixer
import subprocess
import time
from env import env_device_id, env_directory_data, env_recording_frame_rate, env_recording_sample_rate
from utils_device import calculate_offset_seconds
from utils_files import read_file_json


# FFMPEG
# --- converters
def convert_h264_to_mp4(input_file: str, output_file: str, frame_rate: int):
    command = ["ffmpeg", "-r", str(frame_rate), "-i", input_file, "-c:v", "copy", "-c:a", "copy", output_file]
    subprocess.run(command)

def combine_h264_and_wav_into_mp4(video_file_path, audio_file_path, output_file_path):
    logging.info("[combine_h264_and_wav_into_mp4] video: %s + audio: %s = mp4 %s", video_file_path, audio_file_path, output_file_path)
    # --- calc offset since multiprocess
    offset = calculate_offset_seconds(
        read_file_json(video_file_path + '.json')['start_time_sec'],
        read_file_json(audio_file_path + '.json')['start_time_sec'],
    )
    # --- setup command
    command = [
        "ffmpeg",
        "-r", str(env_recording_frame_rate()), # video capture frame rate
        "-i", video_file_path,
        '-itsoffset', str(offset), # offsetting is scuffed
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
    logging.info("[combine_h264_and_wav_into_mp4] command: ", command)
    subprocess.run(command, check=True)

# MEDIA
# --- ids
def generate_media_id() -> str:
    return f"{env_device_id()}-{int(time.time())}"

# --- keys/paths # TODO: could make this kargs spread for joining many props
def get_media_key(media_id, media_format, segment_id = None):
    if segment_id == None:
        return f"{media_id}.{media_format}"
    return f"{media_id}--{segment_id}.{media_format}"

def get_media_local_file_path(media_id, media_format, segment_id = None):
    return f"{env_directory_data()}/{get_media_key(media_id, media_format, segment_id)}"


# AUDIO
AUDIO_CHANNEL_MAIN = 0
# AUDIO_CHANNEL_NOTIFICATIONS = 1 # maybe notifs on separate channel so it can play w/o interrupting main audio

def play_audio(audio_bytes, is_blocking: bool, channel = AUDIO_CHANNEL_MAIN):
    logging.info("[play_audio] playing")
    mixer.init()
    # --- create sound
    sound = mixer.Sound(audio_bytes)
    # --- create channel + play
    channel = mixer.Channel(channel) # must provide id. in the future may need to manage this if doing audio playback + notifications sounds
    channel.set_volume(0.75)
    channel.play(sound, loops=0)
    # --- wait till done playing sound before returning (needed seomtimes bc a process exit stops sound)
    if is_blocking:
        logging.info("[play_audio] busy/blocking")
        while channel.get_busy():
            continue
    logging.info("[play_audio] done")
