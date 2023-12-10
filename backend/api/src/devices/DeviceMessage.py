from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from orm import BaseModel


class DeviceMessage(BaseModel):
    __tablename__ = "device_message"
    id = Column(Integer, primary_key=True)
    device_id = Column(Text())
    type = Column(Text())
    data = Column(JSONB())
    created_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    def serialize(self, serialize_relationships=[]):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "type": self.type,
            "data": self.data,
            "created_at": str(self.created_at),
            "delivered_at": str(self.delivered_at),
        }
