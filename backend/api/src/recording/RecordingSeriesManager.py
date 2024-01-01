import numpy as np
import os
import sqlalchemy as sa
from sqlalchemy.orm import joinedload
from typing import List
from uuid import uuid4
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_path
from file.file_utils import merge_media_files, tmp_file_path, tmp_file_rmv, tmp_file_set
from recording.Recording import Recording
from recording.RecordingAnnotation import RecordingAnnotation
from orm import sa_sessionmaker
from vision.clip import clip_encode, clip_similarity


class RecordingSeriesManager():
    # SETUP/PROPS
    # --- ids
    series_id = None
    # --- recordings
    recordings: List[Recording] = []
    recordings_duration_sec = 0
    transcripts = []
    transcripts_text: str = ""
    transcripts_sentences = []
    # --- annotations
    recording_annotations: List[RecordingAnnotation] = []
    # --- extras loading/processing
    series_recording_file_path: str = None
    series_media_file_url: str = None

    # LOADERRS
    # --- load series (recordings + annotations)
    async def load_series(self, series_id: str) -> None:
        print(f"[RecordingSeriesManager.load_series] load series = {series_id}")
        self.series_id = series_id
        # --- refetch recordings to break reference + ensure we have annotations (TODO: kidna inefficient but w/e. i wonder if a session is reused?)
        session = sa_sessionmaker()
        async with session.begin():
            query_recordings = await session.execute(
                sa.select(Recording)
                    # .options(joinedload(Recording.recording_annotation)) # done via follow up query
                    .where(Recording.series_id == series_id)
                    .order_by(Recording.id.asc()))
            recordings = query_recordings.scalars().unique().all()
        await session.close()
        # --- now set recordings w/ annotations
        await self.load_recordings(recordings)
        # --- load annotations
        await self.load_annotations()
    
    # --- recordings (recordings + annotations)
    async def load_recordings(self, recordings) -> None:
        print(f"[RecordingSeriesManager.load_recordings] num recordings = {len(recordings)}")
        # --- transcript setup
        current_recordings_duration_sec = 0
        for rec_idx in range(len(recordings)): # when i did enumerate that thing ran non-stop
            rec = recordings[rec_idx]
            print(f"[RecordingSeriesManager.load_recordings] processing rec: #{rec_idx}")
            # --- push to text/sentences props
            self.transcripts_text += rec.transcript_text
            # --- update sentences timing values
            for s in rec.transcript_sentences:
                s["adjusted_by_seconds"] = current_recordings_duration_sec
                s["adjusted_second_start"] = s["second_start"] + current_recordings_duration_sec
                s["adjusted_second_end"] = s["second_end"] + current_recordings_duration_sec
                self.transcripts_sentences.append(s)
            # --- update duration floor for mapping next set of sentences
            current_recordings_duration_sec += recordings[rec_idx].media_duration_sec
            # --- push recording
            self.recordings.append(recordings[rec_idx])
        # --- final duration
        self.recordings_duration_sec = current_recordings_duration_sec
        print("[load_recordings] recordings_duration_sec: ", self.recordings_duration_sec)
        # --- load annotations
        await self.load_annotations()

    async def load_annotations(self) -> None:
        print(f"[RecordingSeriesManager.load_annotations] annotations for {len(self.recordings)} recordings")
        session = sa_sessionmaker()
        async with session.begin():
            query_recording_annotations = await session.execute(
                sa.select(RecordingAnnotation)
                    .where(RecordingAnnotation.recording_id.in_([rec.id for rec in self.recordings]))
                    .order_by(RecordingAnnotation.id.asc())) # HACK: this ordering assumption is going to bite me
            recording_annotations = query_recording_annotations.scalars().unique().all()
        await session.close()
        # --- set
        print(f"[RecordingSeriesManager.load_annotations] setting {len(recording_annotations)} annotations on RSM")
        self.recording_annotations = recording_annotations


    # --- selectors/filters for recordings (so we can join on them later)
    def get_recordings_for_described_step(self, query_text: int) -> List[Recording]:
        print(f"[RecordingSeriesManager.get_recordings_for_described_step] query_text: {query_text}")
        # --- see what step_description_text most closely matches out of step descriptions (just gonna reuse clip, its prob good enough)
        step_ras = list(filter(lambda ra: ra.type == "step", self.recording_annotations))
        # --- encode and check similarties
        step_ras_strings = [ra.data.get('text') for ra in step_ras]
        print(f"[RecordingSeriesManager.get_recordings_for_described_step] step_ras_strings: ", step_ras_strings)
        _, step_text_encodings = clip_encode([], step_ras_strings)
        _, query_text_encodings = clip_encode([], [query_text])
        recording_annotation_similarities = clip_similarity(step_text_encodings, query_text_encodings[0]) # returns a list of 0 to 1 values mapping to list arg
        recording_annotation_similarity_idx = np.argmax(recording_annotation_similarities)
        print(f"[RecordingSeriesManager.get_recordings_for_described_step] similarities idx: ", recording_annotation_similarity_idx)
        starting_recording_id = step_ras[recording_annotation_similarity_idx].recording_id
        ending_recording_id = step_ras[recording_annotation_similarity_idx + 1].recording_id if step_ras[recording_annotation_similarity_idx + 1] != None else None
        print(f"[RecordingSeriesManager.get_recordings_for_described_step] start/end recording ids: ", starting_recording_id, ending_recording_id)
        # --- get start/end recording ids for step
        segment_recordings = []
        for rec in self.recordings:
            if rec.id >= starting_recording_id and (rec.id < ending_recording_id if ending_recording_id != None else True):
                segment_recordings.append(rec)
        # --- return
        print(f"[RecordingSeriesManager.get_recordings_for_described_step] segment recordings #{len(segment_recordings)}")
        return segment_recordings
    

    # --- series recording (allow passing in a slice)
    def join_recordings(self, recordings: List[Recording] = None) -> str:
        print("[RecordingSeriesManager.join_recordings] start")
        self.series_recording_file_path = tmp_file_path("series_recording_")
        # --- merge to tmp file on disk (TODO: make this go faster)
        recording_keys = [rec.media_file_key for rec in (recordings)]
        recording_paths = []
        try:
            print("[RecordingSeriesManager.join_recordings] downloading tmp files: ", recording_paths)
            for rk in recording_keys:
                bytes = get_stored_file_bytes(rk)
                path = tmp_file_set(bytes, "mp4")
                recording_paths.append(path)
            # --- merge
            merge_media_files(recording_paths, self.series_recording_file_path)
        finally:
            # --- clean up tmp files needed for merge
            print("[RecordingSeriesManager.join_recordings] cleaning tmp files: ", recording_paths)
            for path in recording_paths:
                tmp_file_rmv(path)

    def join_all_recordings(self) -> str:
        print("[RecordingSeriesManager.join_all_recordings] start")
        return self.join_recordings(self.recordings)

    def remove_series_recording_file(self) -> None:
        if self.series_recording_file_path and os.path.exists(self.series_recording_file_path):
            os.remove(self.series_recording_file_path)
            print(f"[RecordingSeriesManager.remove_series_recording_file] Removed series recording file: {self.series_recording_file_path}")
        # --- clear reference
        self.series_recording_file_path = None

    # --- series recording upload
    def store_series_recording(self) -> str:
        print("[RecordingSeriesManager.store_series_recording] start")
        # --- upload to S3
        series_media_file_key = f"{uuid4()}.mp4"
        store_file_from_path(self.series_recording_file_path, series_media_file_key)
        # --- set URL for easy reference
        self.series_media_file_url = get_stored_file_url(series_media_file_key)
        # --- return
        return series_media_file_key
