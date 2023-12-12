import math
import numpy as np
from emails.fill_email_template_html import fill_email_template_html_tasks_summary
from emails.send_email import send_email
from intake.recording_series_manager import RecordingSeriesManager
from llms.prompts import prompt_recording_transcript_to_task_headers, prompt_recording_transcript_to_task_outline
from vision.clip import clip_encode, clip_similarity
from vision.cv import encode_frame_to_jpg, video_frame_generator


def recording_series_emailer(recordings, to_email):
    print("[recording_series_emailer] start")
    rsm = RecordingSeriesManager()
    # --- transcribe (w/ timestamps on sections) + map timings and things so there's larger context
    rsm.load_recordings(recordings)


    # PROMPT FOR META DATA
    print("[recording_series_emailer] transcripts to headers/titles")
    # --- create outline of what occurred -> text[]
    session_task_headers = prompt_recording_transcript_to_task_headers(rsm.transcripts_text)
    # --- if no task headers, it's unclear that this video is of a protocol. SKIP
    if len(session_task_headers) == 0:
        return

    # --- for each outline sub-header write summary of what happened -> text[][]
    print("[recording_series_emailer] transcripts headers/titles to outline tasks")
    session_task_outline = prompt_recording_transcript_to_task_outline(rsm.transcripts_sentences, session_task_headers)


    # SCAN FOR TASK IMAGES
    try:
        # --- form full recording file
        rsm.join_recordings()
        # --- grab image frames from time points and append to email sections (appending to dict because we need to create html img cid references and file data objs)
        for idx, task in enumerate(session_task_outline):
            print(f"[recording_series_emailer] processing content for task #{idx}", task)

            # --- skip if no timestamps exist for task
            if task.get("taskStartAtSecond") == None or task.get("taskEndAtSecond") == None:
                continue

            # --- get task time point (we're getting it in seconds, but we've mapped the timings on our )
            recording_task_start_second = task['taskStartAtSecond'] - 5
            recording_task_end_second = task['taskEndAtSecond'] + 5
            print(f"[recording_series_emailer] recording_task_start_second: {recording_task_start_second}, recording_task_end_second: {recording_task_end_second}")

            # --- ensure that our task timings make sense since its a generative output
            if recording_task_start_second >= recording_task_end_second or recording_task_start_second > rsm.recordings_duration_sec:
                print(f"[recording_series_emailer] skipping frame grab for task #{idx} because start times are past end time/recording duration")
                continue
            if recording_task_end_second > rsm.recordings_duration_sec: # maybe we should skip here to, but leaving for now
                recording_task_end_second = rsm.recordings_duration_sec - 1 # -1 to prevent out of bounds error

            # --- grab video frame
            frames_for_comparison = []
            # --- compile a frame for each second
            for frame in video_frame_generator(rsm.series_recording_file_path, start_second=recording_task_start_second, stop_second=recording_task_end_second, interval_seconds=1):
                frames_for_comparison.append(frame)
            if len(frames_for_comparison) > 0:
                # --- encode frames with CLIP, as well as task summary to find most associated image for task preview/snapshot
                image_encodings, text_encodings = clip_encode(frames_for_comparison, [task['taskSummary']])
                # --- eval cosine similarity
                image_similarities = clip_similarity(image_encodings, text_encodings[0]) # returns a list of 0 to 1 values mapping to list arg
                # --- eval frames: highest
                highest_image_similarity_idx = np.argmax(image_similarities) # grab index of highest value so we can select for it
                highest_image_similarity_frame_encoded_as_jpg = encode_frame_to_jpg(frames_for_comparison[highest_image_similarity_idx], 30) # compress data (for email)
                # --- associate the best pick with the session obj
                session_task_outline[idx]['images'] = [highest_image_similarity_frame_encoded_as_jpg, ]
                print(f"[recording_series_emailer] task: attached highest image similarity (idx: {highest_image_similarity_idx})")
                # --- eval frames: middle of the road. if we have lots of frames, let's jump to a different frame. might give user more context/new vantage point
                if len(image_similarities) > 15:
                    image_similarities[highest_image_similarity_idx] = 0
                    for i in range (math.floor(len(frames_for_comparison) / 3)): # grab top frame third way in
                        idx_to_clear = np.argmax(image_similarities)
                        image_similarities[idx_to_clear] = 0
                    mid_image_similarity_idx = np.argmax(image_similarities)
                    less_high_image_similarity_frame_encoded_as_jpg = encode_frame_to_jpg(frames_for_comparison[mid_image_similarity_idx], 30)
                    session_task_outline[idx]['images'].append(less_high_image_similarity_frame_encoded_as_jpg)
                    print(f"[recording_series_emailer] task: attached less high image similarity (idx: {mid_image_similarity_idx})")
            else:
                print("[recording_series_emailer] NO FRAMES found for comparison")

        # EMAIL
        # --- convert summary into HTML for email
        email_html = fill_email_template_html_tasks_summary(session_task_outline)
        # --- send email
        send_email(
            to_emails=[to_email],
            subject="Task Summary",
            html=email_html
        )
    finally:
        # CLEAN UP
        # --- series recording
        rsm.remove_series_recording_file()

    print("[recording_series_emailer] done")
    return
