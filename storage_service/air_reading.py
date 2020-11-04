from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


# noinspection SpellCheckingInspection
class AirReading(Base):
    """Air reading"""
    __tablename__ = "air_reading"

    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(250), nullable=False)
    so2 = Column(Integer, nullable=False)
    co = Column(Integer, nullable=False)
    no2 = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, sensor_id, so2, co, no2, timestamp):
        self.sensor_id = sensor_id
        self.so2 = so2
        self.co = co
        self.no2 = no2
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now()

    def to_dict(self):
        dict = {'id': self.id,
                'sensor_id': self.sensor_id,
                'so2': self.so2,
                'co': self.co,
                'no2': self.no2,
                'timestamp': self.timestamp,
                'date_created': self.date_created
                }

        return dict
