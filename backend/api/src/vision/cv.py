import base64
from io import BytesIO
import cv2
import numpy as np


# ENCODINGS
def encode_frame_to_jpg(frame) -> np.ndarray:
    print("[encode_frame_to_jpg] encoding image to JPG")
    success, encoded_image = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80]) # default compression is 95 https://stackoverflow.com/questions/40768621/python-opencv-jpeg-compression-in-memory
    if not success:
        raise ValueError("Could not encode image")
    return encoded_image # numpy.ndarray

# TODO: make this work w/ arrays or pyfiles or other things
def encoded_frame_to_base64(image_ndarray: np.ndarray):
    print("[encoded_image_to_base64] encoding image to base64", image_ndarray)
    buffered = BytesIO(image_ndarray)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


# FRAMES
def video_frame_at_second(file_path, second) -> np.ndarray:
    print("[video_frame_at_second] processing")
    video = cv2.VideoCapture(file_path) # this method needs a file, so create a tmp one if in memory
    fps = video.get(cv2.CAP_PROP_FPS) # convenient we get this from the video container/meta
    # --- set the video position to the calculated frame number
    frame_number = int(second * fps) # calculate frame number based on second and fps
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    video.release()  # Release the video capture object
    # --- return frame
    try:
        if ret:
            frame = cv2.cvtColor(frame, cv2.IMREAD_COLOR)
            # return frame
            # converting to a JPEG byte arr
            frame_encoded_as_jpg = encode_frame_to_jpg(frame)
            return frame_encoded_as_jpg # numpy.ndarray
        else:
            return None
    except Exception as err:
        print("[video_frame_at_second] error: ", err)
        return None

def video_frame_generator(file_path, start_second=0, stop_second=None, interval_seconds=1):
    print("[video_frame_generator] generating frames from {start_second}->{stop_second}, 1 frame per {interval_seconds} seconds")
    # --- open file
    video = cv2.VideoCapture(file_path)
    # --- get/set frames info
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    start_frame = int(start_second * fps)
    stop_frame = int(stop_second * fps) if stop_second else total_frames
    frame_step = 1 if interval_seconds == None else int(interval_seconds * fps) # if no interval by seconds, output each frame
    # --- set starting frame
    video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame
    # --- loop
    while current_frame < stop_frame:
        ret, frame = video.read()
        if not ret:
            break  # break the loop if no more frames are available
        yield frame
        current_frame += frame_step
    # --- release the video capture object
    video.release()
