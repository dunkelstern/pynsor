from typing import Optional, Dict, Any, List
import subprocess
from datetime import datetime

from .sensor import Sensor
from pynsor.postgres import Connection

class RyzenPower(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)
        self.binary_path = config['ryzenpower_binary'] if 'ryzenpower_binary' in config else '/usr/bin/ryzen_power'

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table(
            'power',
            [
                {"name": "power_type", "type": "TEXT", "null": "NOT NULL"},
                {"name": "power", "type": "FLOAT", "null": "NULL"},
            ]
        )
        connection.create_index('power', ('time', 'power_type'))
        connection.create_index('power', 'power_type')

    def gather(self, timestamp: datetime):
        try:
            self.raw_data.append({
                'time': timestamp,
                'data': subprocess.check_output([self.binary_path])
            })
        except subprocess.CalledProcessError as e:
            self.is_enabled = False

    def data(self) -> Optional[List[Dict[str, Any]]]:
        if self.raw_data is None:
            return None

        result = []
        for item in self.raw_data:
            data = {'time': item['time']}

            for line in item['data'].decode('utf-8').splitlines():
                if line.startswith('cpu_power'):
                    cores = line[10:].split(',')
                    data['core'] = {}
                    for core in cores:
                        c, p = core.split('=')
                        p = float(p)
                        data['core'][c] = p
                if line.startswith('package_power'):
                    packages = line[14:].split(',')
                    data['package'] = {}
                    for package in packages:
                        p, v = package.split('=')
                        v = float(v)
                        data['package'][p] = v
            result.append(data)
        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from ryzen power!")
            return

        for item in data:
            timestamp = item['time']
            for t, measurement in item.items():
                if t == 'time':
                    continue
                for sensor_name, value in measurement.items():
                    connection.insert('power', {"time": timestamp, "power_type": f"{t}.{sensor_name}", "power": value})

        self.raw_data = []

Sensor.register(RyzenPower)
