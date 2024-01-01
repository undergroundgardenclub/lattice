from sqlalchemy import Column, ForeignKey, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from orm import BaseModel


class RecordingAnnotation(BaseModel):
    __tablename__ = "recording_annotation"
    id = Column(Integer, primary_key=True)
    device_id = Column(Text())
    series_id = Column(Text())
    type = Column(Text())
    data = Column(JSONB())
    created_at = Column(DateTime(timezone=True))
    recording_id = Column(Integer, ForeignKey("recording.id"))
    recording = relationship("Recording", back_populates="recording_annotation")

    def serialize(self, serialize_relationships=[]):
        return {
            "id": self.id,
            "recording_id": self.recording_id,
            "device_id": self.device_id,
            "series_id": self.device_id,
            "type": self.type,
            "data": self.data,
            "created_at": str(self.created_at),
        }
