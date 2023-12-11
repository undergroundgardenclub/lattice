import json
import time
from utils_api import req_query, req_recording_batch_submit
from utils_device import EVENT_TYPE_SEND_SERIES_RECORDING, EVENT_TYPE_SEND_QUERY_RECORDING
from utils_files import delete_file, store_file_from_path, get_stored_file_url
from utils_media import combine_h264_and_wav_into_mp4, get_media_local_file_path, get_media_key


def processor_sender(process_events, process_queues):
    print('[processor_sender] fork')
    while True:
        # SETUP
        job_type = None
        job_data = None
        # --- check for jobs
        if process_queues["queue_send_recording"].qsize() > 0:
            job = process_queues["queue_send_recording"].get()
            job_type = job["type"]
            job_data = job_data = job.get("data")
        
        # PROCESS
        if job_data != None:
            print(f"[processor_sender] {job_type} =", job_data)
            # MP4 ENCODING
            # --- get keys/paths
            file_path_h264 = job_data.get("file_path_h264")
            file_path_wav = job_data.get("file_path_wav")
            file_key_mp4 = job_data.get("file_key_mp4")
            file_path_mp4 = job_data.get("file_path_mp4")
            file_url_mp4 = get_stored_file_url(file_key_mp4)
            # --- encode mp4s + clean h264/wav files
            combine_h264_and_wav_into_mp4(file_path_h264, file_path_wav, file_path_mp4)
            
            # CLOUD STORAGE
            # --- save file to S3 for reference by backend
            store_file_from_path(file_path_mp4, file_key_mp4)

            # API/REQUEST
            if job_type == EVENT_TYPE_SEND_QUERY_RECORDING:
                req_query(query_file=dict(file_key=file_key_mp4, file_url=file_url_mp4))
            elif job_type == EVENT_TYPE_SEND_SERIES_RECORDING:
                req_recording_batch_submit([dict(file_key=file_key_mp4, file_url=file_url_mp4)])

            # CLEAN
            # --- clean up files (+ meta )
            delete_file(file_path_h264)
            delete_file(file_path_h264 + ".json")
            delete_file(file_path_wav)
            delete_file(file_path_wav + ".json")
            delete_file(file_path_mp4)
        
        # -- continue
        time.sleep(0.01)