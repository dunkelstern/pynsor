from typing import Optional, Dict, Any, List
from datetime import datetime

from .sensor import Sensor
from pynsor.postgres import Connection

class DiskStats(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table(
            'diskstats',
            [
                {"name": "disk", "type": "TEXT", "null": "NOT NULL"},
                {"name": "reads_completed", "type": "BIGINT", "null": "NULL"},
                {"name": "reads_merged", "type": "BIGINT", "null": "NULL"},
                {"name": "sectors_read", "type": "BIGINT", "null": "NULL"},
                {"name": "millis_reading", "type": "BIGINT", "null": "NULL"},
                {"name": "writes_completed", "type": "BIGINT", "null": "NULL"},
                {"name": "writes_merged", "type": "BIGINT", "null": "NULL"},
                {"name": "sectors_written", "type": "BIGINT", "null": "NULL"},
                {"name": "millis_writing", "type": "BIGINT", "null": "NULL"},
                {"name": "io_in_progress", "type": "BIGINT", "null": "NULL"},
                {"name": "millis_io", "type": "BIGINT", "null": "NULL"},
                {"name": "weighted_millis_io", "type": "BIGINT", "null": "NULL"},
                {"name": "discards_completed", "type": "BIGINT", "null": "NULL"},
                {"name": "discards_merged", "type": "BIGINT", "null": "NULL"},
                {"name": "sectors_discarded", "type": "BIGINT", "null": "NULL"},
                {"name": "millis_discarding", "type": "BIGINT", "null": "NULL"}
            ]
        )

        connection.create_index('diskstats', 'disk')

    def gather(self, timestamp: datetime):
        try:
            with open('/proc/diskstats', 'r') as fp:
                self.raw_data.append({
                    "time": timestamp,
                    "data": fp.read()
                })
        except FileNotFoundError:
            pass

    def data(self) -> Optional[List[Dict[str, Any]]]:
        if self.raw_data is None:
            return None
        
        result = []

        for item in self.raw_data:
            data = {}
            for line in item['data'].splitlines():
                input = line.split()
                data[input[2]] = {
                    "time":               item['time'],
                    "disk":               input[2],
                    "reads_completed":    int(input[ 3]),
                    "reads_merged":       int(input[ 4]),
                    "sectors_read":       int(input[ 5]),
                    "millis_reading":     int(input[ 6]),
                    "writes_completed":   int(input[ 7]),
                    "writes_merged":      int(input[ 8]),
                    "sectors_written":    int(input[ 9]),
                    "millis_writing":     int(input[10]),
                    "io_in_progress":     int(input[11]),
                    "millis_io":          int(input[12]),
                    "weighted_millis_io": int(input[13]),
                    "discards_completed": int(input[14]),
                    "discards_merged":    int(input[15]),
                    "sectors_discarded":  int(input[16]),
                    "millis_discarding":  int(input[17]),
                }
            result.append(data)

        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from /proc/diskstats!")
            return

        for item in data:
            for measurement in item.values():
                connection.insert('diskstats', measurement)
        self.raw_data = []

Sensor.register(DiskStats)
