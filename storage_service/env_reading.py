from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


# noinspection SpellCheckingInspection
class EnvReading(Base):
    """Environment reading"""
    __tablename__ = "env_reading"

    id = Column(Integer, primary_key=True)
    sensor_id = Column(String(250), nullable=False)
    humidity = Column(String(250), nullable=False)
    temp = Column(Integer, nullable=False)
    wind_speed = Column(Integer, nullable=False)
    wind_dir = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, sensor_id, humidity, temp, wind_speed,
                 wind_dir, timestamp):
        self.sensor_id = sensor_id
        self.humidity = humidity
        self.temp = temp
        self.wind_speed = wind_speed
        self.wind_dir = wind_dir
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now()

    def to_dict(self):
        dict = {'id': self.id,
                'sensor_id': self.sensor_id,
                'humidity': self.humidity,
                'temp': self.temp,
                'wind_speed': self.wind_speed,
                'wind_dir': self.wind_dir,
                'timestamp': self.timestamp,
                'date_created': self.date_created}

        return dict
