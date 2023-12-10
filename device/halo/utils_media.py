from pygame import mixer
import subprocess
import time
from env import env_device_id, env_directory_data, env_recording_frame_rate, env_recording_sample_rate
from utils_files import read_file_json


# FFMPEG
# --- mapping/helpers
def calculate_offset_seconds(first_ns, second_ns):
    offset = (second_ns - first_ns) / 1e9
    return offset

# --- converters
def convert_h264_to_mp4(input_file: str, output_file: str, frame_rate: int):
    command = ["ffmpeg", "-r", str(frame_rate), "-i", input_file, "-c:v", "copy", "-c:a", "copy", output_file]
    subprocess.run(command)

def combine_h264_and_wav_into_mp4(video_file_path, audio_file_path, output_file_path):
    # --- calc offset since multiprocess
    offset = calculate_offset_seconds(
        read_file_json(video_file_path + '.json')['start_time_ns'],
        read_file_json(audio_file_path + '.json')['start_time_ns'],
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
    subprocess.run(command, check=True)

# MEDIA
# --- ids
def generate_media_id():
    return f"{env_device_id()}-{int(time.time())}"

# --- keys/paths # TODO: could make this kargs spread for joining many props
def get_media_key(media_id, media_format, media_chunk_num = None):
    if media_chunk_num == None:
        return f"{media_id}.{media_format}"
    return f"{media_id}--{media_chunk_num}.{media_format}"

def get_media_local_file_path(media_id, media_format, media_chunk_num = None):
    return f"{env_directory_data()}/{get_media_key(media_id, media_format, media_chunk_num)}"


# AUDIO
def play_audio(audio_bytes, is_blocking=True):
    print("[play_audio] playing")
    mixer.init()
    # --- create sound
    sound = mixer.Sound(audio_bytes)
    # --- create channel + play
    channel = mixer.Channel(0) # must provide id. in the future may need to manage this if doing audio playback + notifications sounds
    channel.set_volume(0.65)
    channel.play(sound, loops=0)
    # --- wait till done playing sound before returning (needed seomtimes bc a process exit stops sound)
    if is_blocking:
        print("[play_audio] busy/blocking")
        while channel.get_busy():
            continue
    print("[play_audio] done")