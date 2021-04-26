from typing import Optional, Dict, Any, List
import subprocess
from datetime import datetime

from .sensor import Sensor
from pynsor.postgres import Connection

class LMSensors(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)
        self.binary_path = config['sensors_binary'] if 'sensors_binary' in config else '/usr/bin/sensors'
        self.use_fallback = config['use_fallback']

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table(
            'temps',
            [
                {"name": "temp_type", "type": "TEXT", "null": "NOT NULL"},
                {"name": "temp", "type": "FLOAT", "null": "NULL"},
            ]
        )
        connection.create_index('temps', ('time', 'temp_type'))
        connection.create_index('temps', 'temp_type')

        connection.create_table(
            'voltage',
            [
                {"name": "voltage_type", "type": "TEXT", "null": "NOT NULL"},
                {"name": "voltage", "type": "FLOAT", "null": "NULL"},
            ]
        )
        connection.create_index('voltage', ('time', 'voltage_type'))
        connection.create_index('voltage', 'voltage_type')

        connection.create_table(
            'fans',
            [
                {"name": "fan_type", "type": "TEXT", "null": "NOT NULL"},
                {"name": "speed", "type": "FLOAT", "null": "NULL"},
            ]
        )
        connection.create_index('fans', ('time', 'fan_type'))
        connection.create_index('fans', 'fan_type')

        connection.create_table(
            'current',
            [
                {"name": "current_type", "type": "TEXT", "null": "NOT NULL"},
                {"name": "current", "type": "FLOAT", "null": "NULL"},
            ]
        )
        connection.create_index('current', ('time', 'current_type'))
        connection.create_index('current', 'current_type')

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
        if self.use_fallback:
            return self.gather_fallback(timestamp)
        try:
            self.raw_data.append({
                'time': timestamp,
                'data': subprocess.check_output([self.binary_path, '-u', '-A'])
            })
        except subprocess.CalledProcessError:
            return self.gather_fallback(timestamp)

    def gather_fallback(self, timestamp: datetime):
        # TODO: PSUtil Fallback
        self.is_enabled = False

    def data(self) -> Optional[List[Dict[str, Any]]]:
        if self.raw_data is None:
            return None

        result = []

        for item in self.raw_data:
            data = {'time': item['time']}
            current_sensor = None
            current_input = None

            for line in item['data'].decode('utf-8').splitlines():
                if len(line) == 0:
                    continue
                if line[0] != ' ' and line[-1] != ':':
                    # new sensor cluster/chip
                    if current_sensor is not None:
                        data[current_sensor] = sensor_data
                    sensor_data = {}
                    current_sensor = line

                if line[0] != ' ' and line[-1] == ':':
                    # new input
                    current_input = line[:-1]

                if line[0] == ' ' and '_input' in line:
                    # found the current value
                    name, value = line.strip().split(":")
                    value = float(value)
                    if current_input not in sensor_data:
                        sensor_data[current_input] = {}
                    sensor_data[current_input][name] = value

            if current_input is not None:
                data[current_sensor] = sensor_data

        result.append(data)

        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from lm_sensors!")
            return

        for item in data:
            timestamp = item['time']
            for chip, measurement in item.items():
                if chip == 'time':
                    continue

                for sensor_name, values in measurement.items():
                    input = list(values.keys())[0]
                    value = values[input]

                    if input.startswith('temp'):
                        self.insert_temp(timestamp, chip, sensor_name, value, connection)
                    elif input.startswith('in'):
                        self.insert_voltage(timestamp, chip, sensor_name, value, connection)
                    elif input.startswith('fan'):
                        self.insert_fan(timestamp, chip, sensor_name, value, connection)
                    elif input.startswith('curr'):
                        self.insert_current(timestamp, chip, sensor_name, value, connection)
                    elif input.startswith('power'):
                        self.insert_power(timestamp, chip, sensor_name, value, connection)
        self.raw_data = []

    def insert_temp(self, time: datetime, chip:str, sensor_name: str, value: float, connection:Connection) -> None:
        connection.insert('temps', {"time": time, "temp_type": f"{chip}.{sensor_name}", "temp": value})

    def insert_voltage(self, time: datetime, chip:str, sensor_name: str, value: float, connection:Connection) -> None:
        connection.insert('voltage', {"time": time, "voltage_type": f"{chip}.{sensor_name}", "voltage": value})

    def insert_fan(self, time: datetime, chip:str, sensor_name: str, value: float, connection:Connection) -> None:
        connection.insert('fans', {"time": time, "fan_type": f"{chip}.{sensor_name}", "speed": value})

    def insert_current(self, time: datetime, chip:str, sensor_name: str, value: float, connection:Connection) -> None:
        connection.insert('current', {"time": time, "current_type": f"{chip}.{sensor_name}", "current": value})

    def insert_power(self, time: datetime, chip:str, sensor_name: str, value: float, connection:Connection) -> None:
        connection.insert('power', {"time": time, "power_type": f"{chip}.{sensor_name}", "power": value})

Sensor.register(LMSensors)
