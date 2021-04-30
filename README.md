# Pynsor - Script to insert monitoring data into a Timescale DB

This project should be an equivalent to [telegraf](https://www.influxdata.com/time-series-platform/telegraf/)
but for the PostgreSQL based [TimescaleDB](https://www.timescale.com/)

## Requirements

- Python >= 3.7
- python `psutil` package
- python `psycopg2` package
- python `tomlkit` package

Optional:

- Ryzen power binary to read out per core energy consumption on Ryzen/Threadripper
  based chips (see [Ryzen Power](https://github.com/dunkelstern/ryzen_power)
- `ss` from `iproute2` for netstat (TCP Statistics)
- `sensors` from `lm_sensors` for pretty sensor readouts (with named fields),
  falls back to `psutil` method if not available
- `smartctl` from `smartmontools` for HDD and SSD SMART monitoring

## Changelog

### 1.1.0 Smartctl

- Add SMART monitoring for HDDs, SSDs and NVME devices

### 1.0.0 Initial release

- Initial release

## Installation

1. Install with `pip install pynsor`
2. Create config file in `/etc/pynsor/pynsor.conf`, for example config see
   `archlinux/pynsor.conf`
3. Start with `pynsor --config /etc/pynsor/pynsor.conf`

All tables needed by the plugins that have been activated are created on
startup automatically (including their hypertables and some indices that
make sense).

If you want to run this as a `systemd` service, see `archlinux/pynsor.service`
for example unit file.


## Configuration

Configuration is a single file that looks like this:

```toml
[global]
refresh = 10
batch_size = 1

[db]
host = "localhost"
port = 5432
username = "monitoring"
password = "monitoring"
db = "monitoring"

[sensor.DiskStats]
enabled = true

[sensor.LMSensors]
enabled = true
sensors_binary = "/usr/bin/sensors"
use_fallback = false

[sensor.Netstat]
enabled = true
ss_binary = "/usr/bin/ss"

[sensor.PSUtil]
enabled = true

[sensor.RyzenPower]
enabled = false
ryzenpower_binary = "/usr/bin/ryzen_power"

[sensor.ProcStat]
enabled = true

[sensor.SMARTCtl]
enabled = true
```

- `global.refresh` defines how often to fetch a sensor reading (seconds)
- `global.batch_size` if not set to `1`, collect `n` readings before writing
  all of them to the DB... May conserve power by not stressing the DB too often.
- `db` should be self explanatory
- The `sensor` namespace is reserved for sensor configuration. The names of the
  sensors are the python class names of the implementation. All sensors have
  at least the `enabled` attribute which defaults to `true` and can be set to
  `false` to disable running that particular sensor

  
## Available Plugins

### DiskStats

- Source: `/proc/diskstats`
- Table: `diskstats`
- Purpose: Disk performance counters

### LMSensors

- Source: `lm_sensors` or `sysfs` hwmon nodes (when used via `psutil` fallback)
- Tables: `temps`, `voltage`, `fans`, `current`, `power`
- Purpose: Active readout of sensors built into the computer

This plugin has a configuration:

- `sensors_binary`: path to the `sensors` binary to use
- `use_fallback`: fall-back to `psutil` even if `lm_sensors` is installed

### Netstat

- Source: `iproute2` binary `ss`
- Table: `netstat`
- Purpose: TCP networking statistics (established sockets, error states, etc.)

This plugin has a configuration:

- `ss_binary`: path to the `ss` binary to use

### PSUtil

- Source: Various readings from `/proc` and `/sys`
- Tables: `cpu_usage`, `cpu_freq`, `load_avg`, `processes`, `virtual_memory`,
  `swap_memory`, `disk_usage`, `net_io_counters`, `disk_io_counters`
- Purpose: Kernel statistics of differing origins

### RyzenPower

- Source: `ryzen_power` binary which reads CPU registers
- Tables: `power`
- Purpose: Read per-core and -package power usage from AMD Ryzen based CPUs

This plugin has a configuration:

- `ryzenpower_binary`: path to the `ryzen_power` binary to use (attention:
  this one is a SUID-root binary!)  

### ProcStat

- Source: `/proc/stat`
- Tables: `cpu_usage_counters`, `kernel`
- Purpose: RAW CPU usage counters and some other kernel information from the
  kernel stats.
 
### SMARTCtl

- Source: `smartctl` (device needs to be accessible by script)
- Tables: `sata_smart`, `nvme_smart`
- Purpose: SMART status of disks

This plugin has a configuration:

- `smartctl_binary`: path to the `smartctl` binary to use (or a wrapper script
  that allows the user to access the disk device)
- `disks`: disks to scan, you can use glob patterns (see default), if not set
  defaults to `[ "/dev/sd?", "/dev/sr?", "/dev/hd?", "/dev/nvme?n1" ]`
