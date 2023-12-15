import json
import logging
import time
from utils_api import req_query, req_recording_series_submit, req_tracking_event
from utils_device import EVENT_TYPE_SEND_SERIES_DONE, EVENT_TYPE_SEND_SERIES_RECORDING, EVENT_TYPE_SEND_QUERY_RECORDING
from utils_files import delete_file, store_file_from_path, get_stored_file_url
from utils_media import combine_h264_and_wav_into_mp4, get_media_local_file_path, get_media_key


def processor_sender(process_events, process_queues):
    logging.info('[processor_sender] fork')
    while True:
        # SETUP
        job_type = None
        job_data = None
        # --- check for jobs
        if process_queues["queue_sender"].qsize() > 0:
            job = process_queues["queue_sender"].get()
            job_type = job["type"]
            job_data = job_data = job.get("data")
        
        # SEND
        if job_type != None:
            logging.info("[processor_sender] %s", job_type, job_data)
            # --- api pings
            if job_type == EVENT_TYPE_SEND_SERIES_DONE:
                    req_tracking_event({ "type": "series_done", "data": { "series_id": job_data.get("series_id") } })

            # --- file/recording handling
            if job_type == EVENT_TYPE_SEND_QUERY_RECORDING or job_type == EVENT_TYPE_SEND_SERIES_RECORDING:
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

                # REQUEST
                if job_type == EVENT_TYPE_SEND_QUERY_RECORDING:
                    req_query(query_file=dict(file_key=file_key_mp4, file_url=file_url_mp4), series_id=job_data.get("series_id"))
                elif job_type == EVENT_TYPE_SEND_SERIES_RECORDING:
                    req_recording_series_submit(dict(file_key=file_key_mp4, file_url=file_url_mp4), series_id=job_data.get("series_id"))

                # CLEAN
                # --- clean up files (+ meta )
                delete_file(file_path_h264)
                delete_file(file_path_h264 + ".json")
                delete_file(file_path_wav)
                delete_file(file_path_wav + ".json")
                delete_file(file_path_mp4)

        # -- continue
        time.sleep(0.01)
