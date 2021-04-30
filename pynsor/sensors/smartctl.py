from typing import Optional, Dict, Any, List
import os
import subprocess
import json
from datetime import datetime
from glob import glob

from .sensor import Sensor
from pynsor.postgres import Connection

class SMARTCtl(Sensor):
    def init(self, config: Dict[str, Any]) -> None:
        super().init(config)
        self.binary_path = config.get('smartctl_binary', '/usr/bin/smartctl')
        disks = config.get('disks', ['/dev/hd?', '/dev/sd?', '/dev/sr?', '/dev/nvme?n1'])
        self.disks = []
        for item in disks:
            self.disks.extend(glob(item))

    def fields(self, typ: str):
        fields = {
            'sata': [
                {"name": "disk",                    "type": "TEXT", "null": "NOT NULL"},
                {"name": "model_name",              "type": "TEXT", "null": "NULL"},
                {"name": "firmware_version",        "type": "TEXT", "null": "NULL"},
                {"name": "serial_number",           "type": "TEXT", "null": "NULL"},
                {"name": "smart_status_passed",     "type": "BOOL", "null": "NULL"},
                {"name": "logical_block_size",      "type": "INT",  "null": "NULL"},
                {"name": "physical_block_size",     "type": "INT",  "null": "NULL"},

                {"name": "raw_read_error_rate",     "type": "INT", "null": "NULL"},
                {"name": "throughput_performance",  "type": "INT", "null": "NULL"},
                {"name": "spin_up_time",            "type": "INT", "null": "NULL"},
                {"name": "start_stop_count",        "type": "INT", "null": "NULL"},
                {"name": "reallocated_sector_ct",   "type": "INT", "null": "NULL"},
                {"name": "seek_error_rate",         "type": "INT", "null": "NULL"},
                {"name": "seek_time_performance",   "type": "INT", "null": "NULL"},
                {"name": "power_on_hours",          "type": "INT", "null": "NULL"},
                {"name": "spin_retry_count",        "type": "INT", "null": "NULL"},
                {"name": "power_cycle_count",       "type": "INT", "null": "NULL"},
                {"name": "g_sense_error_rate",      "type": "INT", "null": "NULL"},
                {"name": "power_off_retract_count", "type": "INT", "null": "NULL"},
                {"name": "load_cycle_count",        "type": "INT", "null": "NULL"},
                {"name": "temperature_celsius",     "type": "BIGINT", "null": "NULL"},
                {"name": "reallocated_event_count", "type": "INT", "null": "NULL"},
                {"name": "current_pending_sector",  "type": "BIGINT", "null": "NULL"},
                {"name": "offline_uncorrectable",   "type": "INT", "null": "NULL"},
                {"name": "udma_crc_error_count",    "type": "INT", "null": "NULL"},
                {"name": "disk_shift",              "type": "BIGINT", "null": "NULL"},
                {"name": "loaded_hours",            "type": "INT", "null": "NULL"},
                {"name": "load_retry_count",        "type": "INT", "null": "NULL"},
                {"name": "load_friction",           "type": "INT", "null": "NULL"},
                {"name": "load_in_time",            "type": "INT", "null": "NULL"},
                {"name": "head_flying_hours",       "type": "INT", "null": "NULL"},
                {"name": "calibration_retry_count", "type": "INT", "null": "NULL"},
                {"name": "multi_zone_error_rate",   "type": "INT", "null": "NULL"},
                
                # ssd specific
                {"name": "wear_leveling_count",     "type": "BIGINT", "null": "NULL"},
                {"name": "used_rsvd_blk_cnt_tot",   "type": "BIGINT", "null": "NULL"},
                {"name": "program_fail_cnt_total",  "type": "INT", "null": "NULL"},
                {"name": "erase_fail_count_total",  "type": "INT", "null": "NULL"},
                {"name": "runtime_bad_block",       "type": "INT", "null": "NULL"},
                {"name": "uncorrectable_error_cnt", "type": "INT", "null": "NULL"},
                {"name": "airflow_temperature_cel", "type": "INT", "null": "NULL"},
                {"name": "ecc_error_rate",          "type": "INT", "null": "NULL"},
                {"name": "crc_error_count",         "type": "INT", "null": "NULL"},
                {"name": "por_recovery_count",      "type": "INT", "null": "NULL"},
                {"name": "total_lbas_written",      "type": "BIGINT", "null": "NULL"},

                # dev stats
                {"name": "lbas_written",            "type": "BIGINT", "null": "NULL"},
                {"name": "lbas_read",               "type": "BIGINT", "null": "NULL"},

            ],
            'nvme': [
                {"name": "disk",                      "type": "TEXT", "null": "NOT NULL"},
                {"name": "model_name",                "type": "TEXT", "null": "NULL"},
                {"name": "firmware_version",          "type": "TEXT", "null": "NULL"},
                {"name": "serial_number",             "type": "TEXT", "null": "NULL"},
                {"name": "smart_status_passed",       "type": "BOOL", "null": "NULL"},
                {"name": "logical_block_size",        "type": "INT",  "null": "NULL"},
                
                {"name": "critical_warning",          "type": "INT", "null": "NULL"},
                {"name": "temperature",               "type": "INT", "null": "NULL"},
                {"name": "available_spare",           "type": "INT", "null": "NULL"},
                {"name": "available_spare_threshold", "type": "INT", "null": "NULL"},
                {"name": "percentage_used",           "type": "INT", "null": "NULL"},
                {"name": "data_units_read",           "type": "BIGINT", "null": "NULL"},
                {"name": "data_units_written",        "type": "BIGINT", "null": "NULL"},
                {"name": "host_reads",                "type": "BIGINT", "null": "NULL"},
                {"name": "host_writes",               "type": "BIGINT", "null": "NULL"},
                {"name": "controller_busy_time",      "type": "INT", "null": "NULL"},
                {"name": "power_cycles",              "type": "INT", "null": "NULL"},
                {"name": "power_on_hours",            "type": "INT", "null": "NULL"},
                {"name": "unsafe_shutdowns",          "type": "INT", "null": "NULL"},
                {"name": "media_errors",              "type": "INT", "null": "NULL"},
                {"name": "warning_temp_time",         "type": "INT", "null": "NULL"},
                {"name": "critical_comp_time",        "type": "INT", "null": "NULL"},
            ]
        }
        return fields[typ]

    def create_datamodel(self, connection: Connection) -> None:
        connection.create_table('sata_smart', self.fields('sata'))
        connection.create_index('sata_smart', ('time', 'disk'))
        connection.create_index('sata_smart', 'disk')

        connection.create_table('nvme_smart', self.fields('nvme'))
        connection.create_index('nvme_smart', ('time', 'disk'))
        connection.create_index('nvme_smart', 'disk')
        

    def gather(self, timestamp: datetime):
        for path in self.disks:
            try:
                self.raw_data.append({
                    'time': timestamp,
                    'disk': os.path.basename(path),
                    'data': subprocess.check_output([self.binary_path, '--nocheck', 'standby', '-a', '-l', 'devstat', '-j', path])
                })
            except subprocess.CalledProcessError as e:
                pass

    def data(self) -> Optional[List[Dict[str, Any]]]:
        if self.raw_data is None:
            return None

        result = []
        for item in self.raw_data:
            json_data = json.loads(item['data'])
            data = {
                'data': {
                    'time': item['time'],
                    'disk': item['disk'],
                    'model_name': json_data['model_name'],
                    'firmware_version': json_data['firmware_version'],
                    'serial_number': json_data['serial_number'],
                    'smart_status_passed': json_data['smart_status']['passed'],
                    'logical_block_size': json_data['logical_block_size']
                }
            }

            if json_data['device']['type'] == 'nvme':
                data['type'] = 'nvme_smart'
                for field in self.fields('nvme'):
                    value = json_data['nvme_smart_health_information_log'].get(field['name'], None)
                    if value is not None:
                        data['data'][field['name']] = value

            if json_data['device']['type'] == 'sat':
                data['type'] = 'sata_smart'
                data['data']['physical_block_size'] = json_data['physical_block_size']
                if 'ata_device_statistics' in json_data:
                    for page in json_data['ata_device_statistics']['pages']:
                        if page['name'] == 'General Statistics':
                            for column in page['table']:
                                if column['name'] == 'Logical Sectors Written':
                                    data['data']['lbas_written'] = column['value']
                                if column['name'] == 'Logical Sectors Read':
                                    data['data']['lbas_read'] = column['value']
                for smart_attribute in json_data['ata_smart_attributes']['table']:
                    name = smart_attribute['name'].lower().replace('-', '_')
                    value = smart_attribute['raw']['value']
                    for field in self.fields('sata'):
                        if field['name'] == name:
                            data['data'][name] = value
                            break

            result.append(data)

        return result

    def save(self, connection: Connection) -> None:
        data = self.data()
        if data is None:
            print("ERROR: Could not read sensordata from ryzen power!")
            return

        for item in data:
            connection.insert(
                item['type'],
                item['data']
            )

        self.raw_data = []

Sensor.register(SMARTCtl)
