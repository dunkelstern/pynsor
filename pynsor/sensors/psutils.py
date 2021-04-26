from typing import Optional, Dict, Any, List
import psutil
from datetime import datetime

from .sensor import Sensor
from pynsor.postgres import Connection


class PSUtil(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table(
            'cpu_usage',
            [
                {"name": "core", "type": "INT", "null": "NOT NULL"},
                {"name": "user", "type": "FLOAT", "null": "NULL"},
                {"name": "nice", "type": "FLOAT", "null": "NULL"},
                {"name": "system", "type": "FLOAT", "null": "NULL"},
                {"name": "idle", "type": "FLOAT", "null": "NULL"},
                {"name": "iowait", "type": "FLOAT", "null": "NULL"},
                {"name": "irq", "type": "FLOAT", "null": "NULL"},
                {"name": "softirq", "type": "FLOAT", "null": "NULL"},
                {"name": "steal", "type": "FLOAT", "null": "NULL"},
                {"name": "guest", "type": "FLOAT", "null": "NULL"},
                {"name": "guest_nice", "type": "FLOAT", "null": "NULL"}
            ]
        )
        connection.create_index('cpu_usage', ('time', 'core'))
        connection.create_index('cpu_usage', 'core')

        connection.create_table(
            'cpu_freq',
            [
                {"name": "core", "type": "INT", "null": "NOT NULL"},
                {"name": "frequency", "type": "FLOAT", "null": "NULL"}
            ]
        )
        connection.create_index('cpu_freq', ('time', 'core'))
        connection.create_index('cpu_freq', 'core')

        connection.create_table(
            'load_avg',
            [
                {"name": "load_avg", "type": "FLOAT", "null": "NULL"}
            ]
        )

        connection.create_table(
            'processes',
            [
                {"name": "num_processes", "type": "INT", "null": "NULL"}
            ]
        )

        connection.create_table(
            'virtual_memory',
            [
                {"name": "total", "type": "BIGINT", "null": "NOT NULL"},
                {"name": "available", "type": "BIGINT", "null": "NULL"},
                {"name": "used", "type": "BIGINT", "null": "NULL"},
                {"name": "free", "type": "BIGINT", "null": "NULL"},
                {"name": "active", "type": "BIGINT", "null": "NULL"},
                {"name": "inactive", "type": "BIGINT", "null": "NULL"},
                {"name": "buffers", "type": "BIGINT", "null": "NULL"},
                {"name": "cached", "type": "BIGINT", "null": "NULL"},
                {"name": "shared", "type": "BIGINT", "null": "NULL"},
                {"name": "slab", "type": "BIGINT", "null": "NULL"}
            ]
        )

        connection.create_table(
            'swap_memory',
            [
                {"name": "total", "type": "BIGINT", "null": "NOT NULL"},
                {"name": "used", "type": "BIGINT", "null": "NULL"},
                {"name": "free", "type": "BIGINT", "null": "NULL"},
                {"name": "sin", "type": "BIGINT", "null": "NULL"},
                {"name": "sout", "type": "BIGINT", "null": "NULL"}
            ]
        )

        connection.create_table(
            'disk_usage',
            [
                {"name": "disk", "type": "TEXT", "null": "NOT NULL"},
                {"name": "total", "type": "BIGINT", "null": "NULL"},
                {"name": "used", "type": "BIGINT", "null": "NULL"},
                {"name": "free", "type": "BIGINT", "null": "NULL"},
            ]
        )
        connection.create_index('disk_usage', ('time', 'disk'))
        connection.create_index('disk_usage', 'disk')

        connection.create_table(
            'net_io_counters',
            [
                {"name": "interface", "type": "TEXT", "null": "NOT NULL"},
                {"name": "bytes_sent", "type": "BIGINT", "null": "NULL"},
                {"name": "bytes_recv", "type": "BIGINT", "null": "NULL"},
                {"name": "packets_sent", "type": "BIGINT", "null": "NULL"},
                {"name": "packets_recv", "type": "BIGINT", "null": "NULL"},
                {"name": "errin", "type": "BIGINT", "null": "NULL"},
                {"name": "errout", "type": "BIGINT", "null": "NULL"},
                {"name": "dropin", "type": "BIGINT", "null": "NULL"},
                {"name": "dropout", "type": "BIGINT", "null": "NULL"}
            ]
        )
        connection.create_index('net_io_counters', ('time', 'interface'))
        connection.create_index('net_io_counters', 'interface')

        connection.create_table(
            'disk_io_counters',
            [
                {"name": "disk", "type": "TEXT", "null": "NOT NULL"},
                {"name": "read_count", "type": "BIGINT", "null": "NULL"},
                {"name": "write_count", "type": "BIGINT", "null": "NULL"},
                {"name": "read_bytes", "type": "BIGINT", "null": "NULL"},
                {"name": "write_bytes", "type": "BIGINT", "null": "NULL"},
                {"name": "read_time", "type": "BIGINT", "null": "NULL"},
                {"name": "write_time", "type": "BIGINT", "null": "NULL"},
                {"name": "read_merged_count", "type": "BIGINT", "null": "NULL"},
                {"name": "write_merged_count", "type": "BIGINT", "null": "NULL"},
                {"name": "busy_time", "type": "BIGINT", "null": "NULL"}
            ]
        )
        connection.create_index('disk_io_counters', ('time', 'disk'))
        connection.create_index('disk_io_counters', 'disk')

    def gather(self, timestamp: datetime):
        partitions = psutil.disk_partitions(all=False)
        disk_usage = {}
        for disk in partitions:
            if disk.mountpoint is not None:
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                except PermissionError:
                    continue
                disk_usage[disk.device.replace('/dev/', '')] = usage

        self.raw_data.append({
            'time': timestamp,
            'data': {
                "cpu_usage": psutil.cpu_times_percent(percpu=True),
                "cpu_freq": psutil.cpu_freq(percpu=True),
                "load_avg": psutil.getloadavg(),
                "virtual_memory": psutil.virtual_memory(),
                "swap": psutil.swap_memory(),
                "disk_usage": disk_usage,
                "net_io_counters": psutil.net_io_counters(pernic=True),
                "disk_io_counters": psutil.disk_io_counters(perdisk=True),
                "processes": len(psutil.pids())
            } 
        })

        battery = psutil.sensors_battery()
        if battery is not None:
            self.raw_data['battery'] = battery

    def data(self) -> Optional[List[Dict[str, Any]]]:
        if self.raw_data is None:
            return None

        result = []

        for item in self.raw_data:

            cpu_usage = [dict(v._asdict()) for v in item['data']['cpu_usage']]
            sum = {}
            i = 0
            for core in cpu_usage:
                for key, value in core.items():
                    if key not in sum:
                        sum[key] = 0
                    sum[key] += value
                core['core'] = i
                core['time'] = item['time']
                i += 1
            for key, value in sum.items():
                sum[key] /= len(item['data']['cpu_usage'])
            sum['time'] = item['time']
            sum['core'] = -1
            cpu_usage.append(sum)

            cpu_freq = []
            i = 0
            for core in item['data']['cpu_freq']:
                cpu_freq.append({
                    "core": i,
                    "time": item['time'],
                    "frequency": core.current
                })
                i += 1

            disk_usage = []
            for disk, usage in item['data']['disk_usage'].items():
                disk_dict = dict(usage._asdict())
                disk_dict['disk'] = disk
                disk_dict['time'] = item['time']
                del disk_dict['percent']
                disk_usage.append(disk_dict)

            net_io = []
            for interface, io in item['data']['net_io_counters'].items():
                net = dict(io._asdict())
                net['interface'] = interface
                net['time'] = item['time']
                net_io.append(net)

            disk_io = []
            for disk, io in item['data']['disk_io_counters'].items():
                disk_dict = dict(io._asdict())
                disk_dict['disk'] = disk
                disk_dict['time'] = item['time']
                disk_io.append(disk_dict)

            virtual_memory = dict(item['data']['virtual_memory']._asdict())
            virtual_memory['time'] = item['time']
            del virtual_memory['percent']

            swap = dict(item['data']['swap']._asdict())
            swap['time'] = item['time']
            del swap['percent']

            data = {
                "cpu_usage":       cpu_usage,
                "cpu_freq":        cpu_freq,
                "load_avg":        {'time': item['time'], 'load_avg': item['data']['load_avg'][0]},
                "virtual_memory":  virtual_memory,
                "swap_memory":     swap,
                "disk_usage":      disk_usage,
                "net_io_counters": net_io,
                "disk_io_counters": disk_io,
                "processes":        {'time': item['time'], 'num_processes': item['data']['processes']}
            }
        
            result.append(data)

        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from psutils!")
            return

        for item in data:
            for table, measurement in item.items():
                if isinstance(measurement, list):
                    for item in measurement:
                        connection.insert(table, item)
                else:
                    connection.insert(table, measurement)

        self.raw_data = []

Sensor.register(PSUtil)
