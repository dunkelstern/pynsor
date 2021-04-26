from typing import Dict, Any

import os
import argparse
from time import sleep
from tomlkit import parse
from pprint import pprint

from .sensors import Sensor
from .postgres import DB

def run(config: Dict[str, Any]) -> None:

    db = DB(config['db'])
    Sensor.init_all(db, config['sensor'])
    Sensor.gather_all()
    while True:
        Sensor.save_all(db)
        for i in range(0, config['global']['batch_size']):
            Sensor.gather_all()
            sleep(config['global']['refresh'])

def init():
    parser = argparse.ArgumentParser(description='Monitor sensors and write measurements to TimescaleDB')
    parser.add_argument(
        '-c', '--config',
        type=str,
        dest='configfile',
        default='/etc/pynsor/pynsor.conf',
        help="Location of the config file (toml format)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.configfile):
        print(f"Could not open config file {args.configfile}")
        exit(1)
    
    with open(args.configfile, 'r') as fp:
        config = parse(fp.read())

    print("Loaded config:")
    pprint(config)
    run(config)


if __name__ == "__main__":
    init()
