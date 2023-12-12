from typing import List
from intake.Recording import Recording
from voice.speech_to_text import speech_to_text


class RecordingSeriesManager():
    # SETUP/PROPS
    recordings: List[Recording] = []
    recordings_duration_sec = 0
    transcripts = []
    transcripts_text: str = ""
    transcripts_sentences = []

    # LOADERRS
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

    # HELPERS
    # --- grab recording files after times were mapped
    def get_recording_file_at_adjusted_second(self, second: int) -> dict:
        at_sec = 0
        for rec in self.recordings:
            if at_sec <= second and second <= (at_sec + rec.recording_duration_sec):
                print(f"FOUND, second = {second}, at_sec = {at_sec}", rec.transcript_sentences)
                return rec
            at_sec += rec.recording_duration_sec

    def get_recorded_file_second_from_adjusted_second(self, second: int) -> int:
        """
        Returns the number of seconds into a recording file. The "second" argument provided is across a series of videos.
        Ex: if second=70, and our recordings are 60 sec chunks, this function will return 10
        """
        at_sec = 0
        # --- scan for recording file we're in, based on their durations
        for rec in self.recordings:
            # --- subtract second from (at_sec + recording_duration_sec) to get the diff
            if at_sec <= second and second <= (at_sec + rec.recording_duration_sec):
                return second - at_sec # doing subtraction, because we want to remove the total prior recording time
            # --- if we're not in the block, continue on
            at_sec += rec.recording_duration_sec

    # --- calcs
    def calc_second_between (self, second_start: int, second_end: int) -> int:
        return second_start + ((second_end - second_start) / 2)
