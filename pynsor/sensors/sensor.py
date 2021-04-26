from __future__ import annotations
from typing import Dict, Any, List, Optional
from pynsor.postgres import DB, Connection
from datetime import datetime

class Sensor:
    registry: List[Sensor] = []

    def __init__(self):
        self.raw_data = []

    def init(self, config: Dict[str, Any]) -> None:
        self.is_enabled = True
        if 'enabled' in config and config['enabled'] is False:
            self.is_enabled = False

    def gather(self, timestamp: datetime):
        raise NotImplemented("Has to be overridden by sensor subclass")

    def data(self) -> Optional[Dict[str, Any]]:
        raise NotImplemented("Has to be overridden by sensor subclass")

    def save(self, connection: Connection) -> None:
        raise NotImplemented("Has to be overridden by sensor subclass")

    def create_datamodel(self, connection: Connection) -> None:
        raise NotImplemented("Has to be overridden by sensor subclass")

    @classmethod
    def register(cls, sensor_class: type) -> None:
        print(f"Registering {sensor_class.__name__}...")
        cls.registry.append(sensor_class())

    @classmethod
    def init_all(cls, db: DB, config: Dict[str, Any]) -> None:
        with db.connect() as cursor:
            for item in cls.registry:
                item.init(config[item.__class__.__name__])
                if item.is_enabled:
                    item.create_datamodel(cursor)

    @classmethod
    def gather_all(cls) -> None:
        t = datetime.now()
        for item in cls.registry:
            if item.is_enabled:
                item.gather(t)

    @classmethod
    def save_all(cls, db: DB) -> None:
        with db.connect() as cursor:
            for item in cls.registry:
                if item.is_enabled:
                    item.save(cursor)
