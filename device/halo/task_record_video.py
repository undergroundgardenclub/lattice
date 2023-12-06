from picamera2 import Picamera2 # my board needed picamera2, picamera had an err
from picamera2.encoders import H264Encoder, Quality
import sys
import time
from env import env_recording_frame_rate

# SETUP
# --- peripheral: Camera/Video (https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
video_encoder = H264Encoder(bitrate=10000000)
video_frame_rate = env_recording_frame_rate()
video_frame_duration_limit = int(1_000_000 / video_frame_rate) # check manual for this recipocal calc
video_size = (1280, 720) # (1600, 900) seems great, (1920, 1080) is big if recording long term, (1280, 720) seemed blurry with movement is a hinderance. err'ing to start on higher quality


# LOOP
def task_record_video(process_events, media_path_video_h264):
    print('[process] task_record_video: fork')
    # START
    with Picamera2() as picam2:
        picam2_config = picam2.create_video_configuration({ 'size': video_size }, controls={"FrameDurationLimits": (video_frame_duration_limit, video_frame_duration_limit)})
        picam2.configure(picam2_config)
        # recording kicks off at paths provided by caller (that way post-recording, files can be modified and later removed)
        picam2.start_recording(video_encoder, output=media_path_video_h264, quality=Quality.MEDIUM)
        while process_events['event_stop_recording'].is_set() == False:
            continue # noop, i tried doing a sleep command to reduce CPU load but it messed with timing i think

    # EXIT
    # --- stop recording to save file
    picam2.stop_recording()
    # --- convert (MOVED UP. we're going to use ffmpeg when we have audio+video so avoid duplicating mp4s)
    # convert_h264_to_mp4(media_path_video_h264, media_path_video_mp4, video_frame_rate)
    # --- exit
    print('[process] task_record_video: exit')
    sys.exit(0)
