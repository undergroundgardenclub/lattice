from typing import List
from emails.email_html_templates import html_template_step_section, html_template_steps_body
from llms.prompts import prompt_image_prompts, prompt_simple_attributes_list, prompt_simple_summary, prompt_simple_title
from recording.Recording import Recording
from recording.RecordingSeriesManager import RecordingSeriesManager


async def _recordings_html_summarizer_from_annotations(recordings_by_step) -> str:
    print("[_recordings_html_summarizer_from_annotations] start")
    steps_html_fragments = []
    # ... for each recording step
    for rbs in recordings_by_step:
        step_rsm = RecordingSeriesManager()

        # Uncomment if I need to inspect some section's html output
        # if rbs.get("step").id != 45:
        #     print("SKIPPING STEP: ", rbs.get("step").id)
        #     continue

        try:
            await step_rsm.load_recordings(rbs.get("recordings"))
            # --- generate header (TODO: annotation text should be cleaned up already???)
            header_text = prompt_simple_title(rbs.get("step").data.get("text"))
            # --- generate summary/actions/bullets
            summary_text = prompt_simple_summary(step_rsm.transcripts_text)
            attributes_list = prompt_simple_attributes_list(step_rsm.transcripts_text)
            image_prompts_list = prompt_image_prompts(step_rsm.transcripts_text, "Only provide 3 prompts using 10 words or less. DO NOT mention people or reference 'people' doing things.")
            # --- generate video of segment + frames
            step_rsm.join_all_recordings()
            step_recording_frames = step_rsm.get_frames(interval_seconds=5)
            # --- get relevant frames
            image_frames = []
            for image_prompt in image_prompts_list:
                prompt_image_frames = step_rsm.get_frames_query(query_text=image_prompt, blur_threshold=15, frames=step_recording_frames)
                if prompt_image_frames[0] is not None:
                    image_frames += prompt_image_frames[:1]
            image_frames_as_jpgs = step_rsm.encode_frames_as(image_frames, "jpg", 12)
            # --- store the video file for reference in email
            step_rsm.store_series_recording()
            # --- form html
            step_html = html_template_step_section(
                header_text=header_text,
                summary_text=summary_text,
                attributes_list=attributes_list,
                video_url=step_rsm.series_media_file_url,
                image_frame_jpgs=image_frames_as_jpgs
            )
            steps_html_fragments.append(step_html)
        finally:
            step_rsm.remove_series_recording_file()
    # RETURN
    # --- generate title
    summarized_header = prompt_simple_title(".".join(map(lambda rbs: rbs.get("step").data.get("text"), recordings_by_step)))
    # --- join
    steps_html = html_template_steps_body(steps_html_fragments, title=summarized_header)
    return steps_html


async def recordings_html_summarizer(recordings: List[Recording]) -> str:
    print("[recordings_html_summarizer] start")
    rsm = RecordingSeriesManager()
    # --- load data + check if we have annotations for steps
    await rsm.load_recordings(recordings)
    recordings_by_step = rsm.get_recordings_by_step()
    print(f"[_recordings_html_summarizer_from_annotations] recordings_by_step ({len(recordings_by_step)} groupings)")
    # --- summarize
    if len(rsm.recording_annotations) > 0:
        return await _recordings_html_summarizer_from_annotations(recordings_by_step)
    else:
        raise BaseException("No annotations found marking steps/sections")
