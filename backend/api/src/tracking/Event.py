from sqlalchemy import Column, DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from orm import BaseModel


class Event(BaseModel):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    type = Column(Text())
    device_id = Column(Text())
    data = Column(JSONB())
    created_at = Column(DateTime(timezone=True))

    def serialize(self, serialize_relationships=[]):
        return {
            "id": self.id,
            "type": self.device_id,
            "device_id": self.device_id,
            "data": self.data,
            "created_at": str(self.created_at),
        }
