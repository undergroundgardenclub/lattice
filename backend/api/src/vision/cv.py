import base64
from io import BytesIO
import cv2
import numpy as np


def video_frame_at_second(path, second) -> np.ndarray:
    print("[video_frame_at_second] processing")
    video = cv2.VideoCapture(path)
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
            # converting to a JPEG rather than byte arr
            success, encoded_image = cv2.imencode('.jpg', frame) 
            if not success:
                raise ValueError("Could not encode image")
            print("[video_frame_at_second] encoded image to JPG", encoded_image)
            return encoded_image # numpy.ndarray
        else:
            return None
    except Exception as err:
        print("[video_frame_at_second] error: ", err)
        return None

# TODO: make this work w/ arrays or pyfiles or other things
def encoded_frame_to_base64(image_ndarray: np.ndarray):
    print("[encoded_image_to_base64] encoding image to base64", image_ndarray)
    buffered = BytesIO(image_ndarray)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
