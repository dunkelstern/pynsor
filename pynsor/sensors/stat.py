from typing import Optional, Dict, Any, List
from datetime import datetime

from .sensor import Sensor
from pynsor.postgres import Connection


class ProcStat(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table(
            'cpu_usage_counter',
            [
                {"name": "core", "type": "INT", "null": "NOT NULL"},
                {"name": "user", "type": "BIGINT", "null": "NULL"},
                {"name": "nice", "type": "BIGINT", "null": "NULL"},
                {"name": "system", "type": "BIGINT", "null": "NULL"},
                {"name": "idle", "type": "BIGINT", "null": "NULL"},
                {"name": "iowait", "type": "BIGINT", "null": "NULL"},
                {"name": "irq", "type": "BIGINT", "null": "NULL"},
                {"name": "softirq", "type": "BIGINT", "null": "NULL"},
                {"name": "steal", "type": "BIGINT", "null": "NULL"},
                {"name": "guest", "type": "BIGINT", "null": "NULL"},
                {"name": "guest_nice", "type": "BIGINT", "null": "NULL"}
            ]
        )
        connection.create_index('cpu_usage_counter', ('time', 'core'))
        connection.create_index('cpu_usage_counter', 'core')

        connection.create_table(
            'kernel',
            [
                {"name": "interrupts", "type": "BIGINT", "null": "NULL"},
                {"name": "context_switches", "type": "BIGINT", "null": "NULL"},
                {"name": "processes_forked", "type": "BIGINT", "null": "NULL"},
                {"name": "processes_running", "type": "BIGINT", "null": "NULL"},
                {"name": "processes_blocked", "type": "BIGINT", "null": "NULL"},
                {"name": "soft_interrupts", "type": "BIGINT", "null": "NULL"}
            ]
        )

    def gather(self, timestamp: datetime):
        try:
            with open('/proc/stat', 'r') as fp:
                self.raw_data.append({
                    'time': timestamp,
                    'data': fp.read()
                })
        except FileNotFoundError:
            self.is_enabled = False

    def data(self) -> Optional[List[Dict[str, Any]]]:
        if self.raw_data is None:
            return None

        result = []

        for item in self.raw_data:

            data = {'cpu_usage_counter': [], 'kernel': {'time': item['time']}}

            for line in item['data'].splitlines():
                input = line.split()
                if input[0].startswith('cpu'):
                    if len(input[0]) == 3:
                        core_id = -1
                    else:
                        core_id = int(input[0][3:])

                    data['cpu_usage_counter'].append({
                        "time":       item['time'],
                        "core":       core_id,
                        "user":       int(input[1]),
                        "nice":       int(input[2]),
                        "system":     int(input[3]),
                        "idle":       int(input[4]),
                        "iowait":     int(input[5]),
                        "irq":        int(input[6]),
                        "softirq":    int(input[7]),
                        "steal":      int(input[8]),
                        "guest":      int(input[9]),
                        "guest_nice": int(input[10]),
                    })
                if input[0] == 'intr':
                    data['kernel']['interrupts'] = int(input[1])
                if input[0] == 'ctxt':
                    data['kernel']['context_switches'] = int(input[1])
                if input[0] == 'processes':
                    data['kernel']['processes_forked'] = int(input[1])
                if input[0] == 'procs_running':
                    data['kernel']['processes_running'] = int(input[1])
                if input[0] == 'procs_blocked':
                    data['kernel']['processes_blocked'] = int(input[1])
                if input[0] == 'softirq':
                    data['kernel']['soft_interrupts'] = int(input[1])

            result.append(data)

        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from /proc/stat!")
            return
        
        for item in data:
            for table, measurement in item.items():
                if isinstance(measurement, list):
                    for item in measurement:
                        connection.insert(table, item)
                else:
                    connection.insert(table, measurement)

        self.raw_data = []

Sensor.register(ProcStat)
