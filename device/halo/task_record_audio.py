import pyaudio
import sys
import time
import wave
from env import env_recording_frame_rate, env_recording_sample_rate
from utils_media import audio_frames_set_volume

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
    # START
    # --- init audio
    audio = pyaudio.PyAudio()
    # --- record
    stream = audio.open(format=audio_format, channels=audio_channels, rate=audio_sample_rate, input=True, frames_per_buffer=audio_chunk)
    frames = []
    while process_events['event_stop_recording'].is_set() == False:
        data = stream.read(audio_chunk)
        frames.append(data)

    # EXIT
    # --- adjust volume (skipping for now to reduce onboard processing)
    # audio_frames_set_volume(frames, 75)
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
    # --- exit
    print('[process] task_record_audio: exit')
    sys.exit(0)