from typing import Optional, Dict, Any, List
import subprocess
from datetime import datetime

from .sensor import Sensor
from pynsor.postgres import Connection


class Netstat(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)
        self.binary_path = config['ss_binary'] if 'ss_binary' in config else '/usr/bin/ss'

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table(
            'netstat',
            [
                {"name": "established", "type": "INT", "null": "NULL"},
                {"name": "syn_sent", "type": "INT", "null": "NULL"},
                {"name": "syn_recv", "type": "INT", "null": "NULL"},
                {"name": "fin_wait1", "type": "INT", "null": "NULL"},
                {"name": "fin_wait2", "type": "INT", "null": "NULL"},
                {"name": "time_wait", "type": "INT", "null": "NULL"},
                {"name": "close", "type": "INT", "null": "NULL"},
                {"name": "close_wait", "type": "INT", "null": "NULL"},
                {"name": "last_ack", "type": "INT", "null": "NULL"},
                {"name": "listen", "type": "INT", "null": "NULL"},
                {"name": "closing", "type": "INT", "null": "NULL"},
                {"name": "unknown", "type": "INT", "null": "NULL"}
            ]
        )

    def gather(self, timestamp: datetime):
        try:
            self.raw_data.append({
                "time": timestamp,
                "data": subprocess.check_output(
                    f'{self.binary_path} -t -H -a -n|cut -d " " -f 1|sort|uniq -c',
                    shell=True
                )
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
                num, typ = line.split()
                if typ == 'ESTAB':
                    data['established'] = int(num)
                if typ == 'LISTEN':
                    data['listen'] = int(num)
                if typ == 'TIME-WAIT':
                    data['time_wait'] = int(num)
                if typ == 'SYN-SENT':
                    data['syn_sent'] = int(num)
                if typ == 'SYN-RECV':
                    data['syn_recv'] = int(num)
                if typ == 'FIN-WAIT1':
                    data['fin_wait1'] = int(num)
                if typ == 'FIN-WAIT2':
                    data['fin_wait2'] = int(num)
                if typ == 'CLOSE':
                    data['close'] = int(num)
                if typ == 'CLOSE-WAIT':
                    data['close_wait'] = int(num)
                if typ == 'LAST-ACK':
                    data['last_ack'] = int(num)
                if typ == 'CLOSING':
                    data['closing'] = int(num)
                if typ == 'UNKNOWN':
                    data['unknown'] = int(num)
            result.append(data)

        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from ss!")
            return
        
        for item in data:
            connection.insert('netstat', item)

        self.raw_data = []


Sensor.register(Netstat)
