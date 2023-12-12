import os
from typing import List
from file.file_cloud_storage import get_stored_file_bytes
from file.file_utils import merge_media_files, tmp_file_path, tmp_file_rmv, tmp_file_set
from intake.Recording import Recording
from voice.speech_to_text import speech_to_text


class RecordingSeriesManager():
    # SETUP/PROPS
    recordings: List[Recording] = []
    recordings_duration_sec = 0
    transcripts = []
    transcripts_text: str = ""
    transcripts_sentences = []
    # --- extras loading/processing
    series_recording_file_path = None

    # LOADERRS
    # --- transcripts/recordings
    def load_recordings(self, recordings) -> None:
        print(f"[load_recordings] num recording = {len(recordings)}")
        # --- transcript setup
        current_recordings_duration_sec = 0
        for rec_idx in range(len(recordings)): # when i did enumerate that thing ran non-stop
            rec = recordings[rec_idx]
            print(f"[load_recordings] processing rec: #{rec_idx}")
            # --- push to text/sentences props
            self.transcripts_text += rec.transcript_text
            # --- update sentences timing values
            for s in rec.transcript_sentences:
                s["adjusted_by_seconds"] = current_recordings_duration_sec
                s["adjusted_second_start"] = s["second_start"] + current_recordings_duration_sec
                s["adjusted_second_end"] = s["second_end"] + current_recordings_duration_sec
                self.transcripts_sentences.append(s)
            # --- update duration floor for mapping next set of sentences
            current_recordings_duration_sec += recordings[rec_idx].recording_duration_sec
            # --- push recording
            self.recordings.append(recordings[rec_idx])
        # --- final duration
        self.recordings_duration_sec = current_recordings_duration_sec
        print("[load_recordings] recordings_duration_sec: ", self.recordings_duration_sec)

    # --- series recording
    def join_recordings(self) -> str:
        print("[join_recordings] start")
        self.series_recording_file_path = tmp_file_path("series_recording_")
        # --- merge to tmp file on disk (TODO: make this go faster)
        recording_keys = [rec.recording_file_key for rec in self.recordings]
        recording_paths = []
        try:
            print("[join_recordings] downloading tmp files: ", recording_paths)
            for rk in recording_keys:
                bytes = get_stored_file_bytes(rk)
                path = tmp_file_set(bytes)
                recording_paths.append(path)
            # --- merge
            merge_media_files(recording_paths, self.series_recording_file_path)
        finally:
            # --- clean up tmp files needed for merge
            print("[join_recordings] cleaning tmp files: ", recording_paths)
            for path in recording_paths:
                tmp_file_rmv(path)

    def remove_series_recording_file(self) -> None:
        if self.series_recording_file_path and os.path.exists(self.series_recording_file_path):
            os.remove(self.series_recording_file_path)
            print(f"Removed series recording file: {self.series_recording_file_path}")
        # --- clear reference
        self.series_recording_file_path = None