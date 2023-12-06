import cv2
import numpy as np
import os
import tempfile


def video_frame_at_second(path, second) -> np.ndarray:
    video = cv2.VideoCapture(path)
    fps = video.get(cv2.CAP_PROP_FPS) # convenient we get this from the video container/meta

    # --- set the video position to the calculated frame number
    frame_number = int(second * fps) # calculate frame number based on second and fps
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    video.release()  # Release the video capture object

    # --- return frame
    if ret:
        frame = cv2.cvtColor(frame, cv2.IMREAD_COLOR)
        # return frame
        # converting to a JPEG rather than byte arr
        success, encoded_image = cv2.imencode('.jpg', frame) 
        if not success:
            raise ValueError("Could not encode image")
        return encoded_image # numpy.ndarray
    else:
        return None
