import pyaudio
import sys
import time
import wave
from env import env_recording_frame_rate, env_recording_sample_rate
from utils_files import write_file_json


# SETUP
# --- peripheral: microphone (doing USB for now)
audio_format = pyaudio.paInt16
audio_channels = 1
audio_sample_rate = env_recording_sample_rate() # 44100 is norm but trying to trim file sizes. also timing is better
audio_frame_rate = env_recording_frame_rate() # how do i get it to match!!?!!??
audio_chunk = 1024


# LOOP
def task_record_audio(process_events, media_path_audio_wav):
    print('[process] task_record_audio: fork')
    start_time_ns = None

    # START
    # --- init audio
    audio = pyaudio.PyAudio()
    # --- record
    stream = audio.open(format=audio_format, channels=audio_channels, rate=audio_sample_rate, input=True, frames_per_buffer=audio_chunk)
    frames = []
    while process_events['event_stop_recording'].is_set() == False:
        # --- on first frame, save metadata
        if start_time_ns == None:
            start_time_ns = time.time_ns()
        # --- push data
        data = stream.read(audio_chunk)
        frames.append(data)

    # EXIT
    # --- stop recording streams/audio instance
    stream.stop_stream()
    stream.close()
    audio.terminate()
    # --- save file
    with wave.open(media_path_audio_wav, 'wb') as wf:
        wf.setnchannels(audio_channels)
        wf.setsampwidth(audio.get_sample_size(audio_format))
        wf.setframerate(audio_sample_rate)
        wf.writeframes(b''.join(frames))
    # --- save meta data file
    write_file_json(media_path_audio_wav + '.json', { 'start_time_ns': start_time_ns })
    # --- exit
    print('[process] task_record_audio: exit')
    sys.exit(0)