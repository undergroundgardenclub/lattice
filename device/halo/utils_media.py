import numpy
import subprocess
from env import env_recording_frame_rate, env_recording_sample_rate

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

# https://stackoverflow.com/questions/71039077/how-can-i-change-the-volume-of-a-stream-playing-in-pyaudio
def audio_frames_set_volume(frames: list, volume: int):
    """ Change value of list of audio chunks """
    sound_level = (volume / 100.)
    for i in range(len(frames)):
        chunk = numpy.fromstring(frames[i], numpy.int16)
        chunk = chunk * sound_level
        frames[i] = chunk.astype(numpy.int16)
