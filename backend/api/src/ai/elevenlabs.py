from pydub import AudioSegment
from io import BufferedReader, BytesIO
import requests
import env

CHUNK_SIZE = 1024

def eleven_labs_text_to_speech(text: str, file_path: str, voice_id="Zlb1dXrM653N07WRdFW3", output_format="mp3_44100_64") -> BytesIO:
    print(f"eleven_labs_text_to_speech: '{text}'")
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": env.env_get_eleven_labs_api_key(),
    }
    json = {
    "text": text,
    "model_id": "eleven_monolingual_v1", # "eleven_turbo_v2",
    "voice_settings": {
        "stability": 0,
        "similarity_boost": 0,
        "style": 0,
        "use_speaker_boost": True
    }
    }
    # Request
    response = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?optimize_streaming_latency=0&output_format={output_format}", headers=headers, json=json)

    # Write all respose chunks to a file (kinda jank saving to disk in this func but w/e)
    audio_io = BytesIO()
    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunk:
            audio_io.write(chunk)
    audio_io.seek(0) # resets file pointer to start for reading later

    # Return BytesIO
    return audio_io


def mp3_to_wav(mp3_iobytes: BytesIO) -> BytesIO:
    print('mp3_to_wav')
    audio = AudioSegment.from_mp3(mp3_iobytes)
    # Create BytesIO obj to hold data
    wav_io = BytesIO()
    # Export audio to as WAV (fyi, this requires an external dependency, check dockerfile)
    audio.export(wav_io, format="wav")
    # Seek to beginning of io
    wav_io.seek(0)
    # Return IO
    return wav_io
