from pygame import mixer
import subprocess
import time
from env import env_device_id, env_recording_frame_rate, env_recording_sample_rate
from utils_files import read_file_json


# FFMPEG
# --- mapping/helpers
def calculate_offset(first_audio_timestamp_ns, first_video_timestamp_ns):
    offset = (first_video_timestamp_ns - first_audio_timestamp_ns) / 1e9
    print('[calculate_offset] offset = ', offset)
    return offset

# --- converters
def convert_h264_to_mp4(input_file: str, output_file: str, frame_rate: int):
    command = ["ffmpeg", "-r", str(frame_rate), "-i", input_file, "-c:v", "copy", "-c:a", "copy", output_file]
    subprocess.run(command)

def combine_h264_and_wav_into_mp4(video_file_path, audio_file_path, output_file_path):
    # --- calc offset since multiprocess
    offset = calculate_offset(
        read_file_json(video_file_path + '.json')['start_time_ns'],
        read_file_json(audio_file_path + '.json')['start_time_ns'],
    )
    # --- setup command
    command = [
        "ffmpeg",
        "-r", str(env_recording_frame_rate()), # video capture frame rate
        "-i", video_file_path,
        '-itsoffset', str(offset), # offsetting audio by 1 second to line up w/ video. looks good!
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
def generate_media_id():
    return f"{env_device_id()}-{int(time.time())}"

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