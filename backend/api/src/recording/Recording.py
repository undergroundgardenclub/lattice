from sqlalchemy import Column, DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from orm import BaseModel


class Recording(BaseModel):
    __tablename__ = "recording"
    id = Column(Integer, primary_key=True)
    device_id = Column(Text())
    series_id = Column(Text())
    created_at = Column(DateTime(timezone=True))
    # --- recording file info
    media_file_key = Column(Text())
    media_file_url = Column(Text())
    media_duration_sec = Column(Float())
    # --- transcript info
    transcript_id = Column(Text()) # uuid provided by assembly ai
    transcript_text = Column(Text())
    transcript_sentences = Column(JSONB())
    transcript_words = Column(JSONB())
    
    def serialize(self, serialize_relationships=[]):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "series_id": self.series_id,
            "created_at": str(self.created_at),
            "media_file_key": self.media_file_key,
            "media_file_url": self.media_file_url,
            "transcript_id": self.transcript_id,
            "transcript_text": self.transcript_text,
            "transcript_sentences": self.transcript_sentences,
            "transcript_words": self.transcript_words,
        }
