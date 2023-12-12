import math
import numpy as np
from emails.fill_email_template_html import fill_email_template_html_tasks_summary
from emails.send_email import send_email
from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import tmp_file_rmv, tmp_file_set
from intake.recording_series_manager import RecordingSeriesManager
from llms.prompts import prompt_recording_transcript_to_task_headers, prompt_recording_transcript_to_task_outline
from vision.clip import clip_encode, clip_similarity
from vision.cv import encode_frame_to_jpg, video_frame_generator


def recording_series_emailer(recordings, to_email):
    print("[recording_series_emailer] start")
    # LOAD/PROCESS RECORDINGS TRANSCRIPTS
    rsm = RecordingSeriesManager()
    # --- transcribe (w/ timestamps on sections) + map timings and things so there's larger context
    rsm.load_recordings(recordings)
    

    # PROMPT FOR META DATA
    print("[recording_series_emailer] transcripts to headers/titles")
    # --- create outline of what occurred -> text[]
    # session_task_headers = prompt_recording_transcript_to_task_headers(rsm.transcripts_text)
    session_task_headers = ['Put Away Dish', 'Turn Off Oven', 'Throw Out Pizza Box', 'Put Away Clothes', 'Organize Piles', 'Fold Pants', 'Relax and Reflect on Timings', 'Clean Up Table', 'Evaluate Annotation System']
    # BREAK: if no task headers, it's unclear that this video is of a protocol, skip processing/email
    if len(session_task_headers) == 0:
        return

    # --- for each outline sub-header write summary of what happened -> text[][]
    print("[recording_series_emailer] transcripts headers/titles to outline tasks")
    # session_task_outline = prompt_recording_transcript_to_task_outline(rsm.transcripts_sentences, session_task_headers)
    session_task_outline = [{'taskName': 'Put Away Dish', 'taskObjective': 'Putting away a dish after cleaning it.', 'taskActions': ['Put away this dish.', 'Should clean it first.', "We're just going to put it away."], 'taskStartAtSecond': 0, 'taskEndAtSecond': 33}, {'taskName': 'Turn Off Oven', 'taskObjective': 'Turning off the oven that was left on.', 'taskActions': ['Turn off this oven left on my oven.'], 'taskStartAtSecond': 13, 'taskEndAtSecond': 33}, {'taskName': 'Throw Out Pizza Box', 'taskObjective': 'Disposing of a pizza box, but deciding to put it on the fridge for now.', 'taskActions': ['Additionally, I need to throw out my pizza box.', "I'll just put that on the fridge, though, now."], 'taskStartAtSecond': 35, 'taskEndAtSecond': 42}, {'taskName': 'Put Away Clothes', 'taskObjective': 'Putting away clothes and getting the laundry bag.', 'taskActions': ['Let me also put away my clothes.', 'Put away some laundry.', 'Should have a lot of laundry.', 'Let me get my laundry bag so I can put that away.'], 'taskStartAtSecond': 44, 'taskEndAtSecond': 85}, {'taskName': 'Organize Piles', 'taskObjective': 'Organizing piles of clothes, with pants on the right and other items on the left.', 'taskActions': ["Other thing task I need to do is organize my piles so I like to have pants on the right, and then I'll usually wear other things on the left."], 'taskStartAtSecond': 186, 'taskEndAtSecond': 212}, {'taskName': 'Fold Pants', 'taskObjective': 'Folding various pairs of pants.', 'taskActions': ["Take out my wallet and headphones and I'll fold my pants.", 'Black pair of pants.', 'Fold my other pair of pants.', "These are the Levi's this time, fold my other panter.", "I don't even know what these are, but they're cool white pants."], 'taskStartAtSecond': 239, 'taskEndAtSecond': 274}, {'taskName': 'Relax and Reflect on Timings', 'taskObjective': 'Relaxing and contemplating the timing challenges faced.', 'taskActions': ['Just relax my blanket, stretch out, relax a little bit and think about how I just challenge with timings.', "I'm not really sure how to deal with that.", "I don't know what to do about those timings."], 'taskStartAtSecond': 274, 'taskEndAtSecond': 316}, {'taskName': 'Clean Up Table', 'taskObjective': 'Cleaning up a small table and disposing of unnecessary items.', 'taskActions': ["Next, I'm going to clean up my little table.", 'Do that.', "I don't need this box anymore.", "I'm going to clear that up.", 'My recycling up here.', "I'm just going to throw away this garbage."], 'taskStartAtSecond': 532, 'taskEndAtSecond': 574}, {'taskName': 'Evaluate Annotation System', 'taskObjective': 'Evaluating and considering improvements for the annotation system.', 'taskActions': ["My last task, I'm going to just be trying to evaluate how to improve the annotation system.", 'But I think this is a good step forward.', 'At least I have this system for pushing click.'], 'taskStartAtSecond': 575, 'taskEndAtSecond': 595}]
    

    # SCAN FOR TASK IMAGES
    # --- grab image frames from time points and append to email sections (appending to dict because we need to create html img cid references and file data objs)
    for idx, task in enumerate(session_task_outline):
        print(f"[recording_series_emailer] processing content for task #{idx}", task)

        # --- skip if no timestamps exist for task
        if task.get("taskStartAtSecond") == None or task.get("taskEndAtSecond") == None:
            continue

        # --- get task time point (we're getting it in seconds, but we've mapped the timings on our )
        sec_between_task = rsm.calc_second_between(task['taskStartAtSecond'], task['taskEndAtSecond'])
        recording = rsm.get_recording_file_at_adjusted_second(sec_between_task)
        # --- offset the task time so it's relative to the file (ex: a task starts 2 seconds into the 3rd recording. so task time may be 120s, but we need to start from 2s)
        recording_task_start_second = rsm.get_recorded_file_second_from_adjusted_second(task['taskStartAtSecond']) - 5 # HACK: trying to grab a few frames before in case prior to speaking an important thing is seen
        recording_task_end_second = rsm.get_recorded_file_second_from_adjusted_second(task['taskEndAtSecond']) + 5
        # TODO IMPORANT TODO this strategy breaks when start/stop moves between two recordings. Needs a new strategy
        

        print(f"[recording_series_emailer] sec_between_task: {sec_between_task}, recording_task_start_second: {recording_task_start_second}, recording_task_end_second: {recording_task_end_second}")
        # --- ensure that our task timings make sense since its a generative output
        if recording_task_start_second >= recording_task_end_second or recording_task_start_second > rsm.recordings_duration_sec:
            print(f"[recording_series_emailer] skipping frame grab for task #{idx} because start times are past end time/recording duration")
            continue
        if recording_task_end_second > rsm.recordings_duration_sec: # maybe we should skip here to, but leaving for now
            recording_task_end_second = rsm.recordings_duration_sec - 1 # -1 to prevent out of bounds error

        # --- grab video frame
        video_file_bytes = get_stored_file_bytes(recording.recording_file_key) # TODO: request.files.get('file') but writing offline atm
        tmp_file_path = tmp_file_set(video_file_bytes) # need file path for OpenCV processing
        try:
            frames_for_comparison = []
            # --- compile a frame for each second
            for frame in video_frame_generator(tmp_file_path, start_second=recording_task_start_second, stop_second=recording_task_end_second, interval_seconds=1):
                frames_for_comparison.append(frame)
            if len(frames_for_comparison) > 0:
                # --- encode frames with CLIP, as well as task summary to find most associated image for task preview/snapshot
                image_encodings, text_encodings = clip_encode(frames_for_comparison, [task['taskObjective']])
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
                    for i in range (math.floor(len(frames_for_comparison) / 3)):
                        idx_to_clear = np.argmax(image_similarities)
                        image_similarities[idx_to_clear] = 0
                    mid_image_similarity_idx = np.argmax(image_similarities)
                    less_high_image_similarity_frame_encoded_as_jpg = encode_frame_to_jpg(frames_for_comparison[mid_image_similarity_idx], 30)
                    session_task_outline[idx]['images'].append(less_high_image_similarity_frame_encoded_as_jpg)
                    print(f"[recording_series_emailer] task: attached less high image similarity (idx: {mid_image_similarity_idx})")
                
            else:
                print("[recording_series_emailer] NO FRAMES found for comparison")
        finally:
            tmp_file_rmv(tmp_file_path)


    # EMAIL 
    # --- convert summary into HTML for email
    email_html = fill_email_template_html_tasks_summary(session_task_outline)

    # --- send email
    send_email(
        to_emails=[to_email],
        subject="Task Summary",
        html=email_html
    )

    print(f"[recording_series_emailer] sent email")
    return
