# NZXT Kraken LCD Temperature Monitor

A Linux daemon for the NZXT Kraken 2024 Elite RGB all-in-one cooler that displays real-time CPU, coolant, and GPU temperatures on the 640×640 LCD, and automatically controls fan speed based on coolant temperature.

## Display

The circular 640×640 LCD shows:

- Left (large): **CPU temperature** + arc progress bar (fills as CPU temp approaches 100°C)
- Top right: **Coolant temperature** (LIQUID)
- Bottom right: **GPU temperature** (GPU)
- Top center: "Linux" decorative label (white italic, static)
- Color coding: < 50°C cyan / 50–70°C yellow / ≥ 70°C red

## Hardware Requirements

| Item | Details |
|------|---------|
| Cooler | NZXT Kraken 2024 Elite RGB (USB ID `1e71:3012`) |
| LCD resolution | 640×640 px (circular screen) |
| GPU | NVIDIA (temperature read via NVML, driver required) |
| CPU | AMD (temperature read via k10temp kernel driver) |
| Firmware | 1.2.0 (tested compatible) |

## Dependencies

```
liquidctl>=1.16.0
Pillow>=12.1.1
```

Install:

```bash
pip install -r requirements.txt
```

System font dependencies (Ubuntu/Debian):

```bash
sudo apt install fonts-dejavu fonts-urw-base35
```

## File Structure

```
run.py                   # Main daemon (signal handling + device init + main loop)
sensor/
├── cpu.py               # CPU temp (reads /sys/class/hwmon, k10temp → Tctl)
├── gpu.py               # GPU temp (ctypes call to libnvidia-ml.so)
└── liquid.py            # Coolant temp (dev.get_status())
screen/
├── render.py            # Temperature color mapping + Pillow image rendering
└── _set_screen_local.py # Local reimplementation of liquidctl KrakenZ3.set_screen()
cooler/
├── pump.py              # Pump fixed at 100%
└── fan_liquid.py        # Fan control (liquid temp curve + moving average + deadband)
```

## Quick Start

### 1. Configure udev rule (allow user access to USB device)

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1e71", MODE="0666", TAG+="uaccess"' \
    | sudo tee /etc/udev/rules.d/71-liquidctl.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 2. Run directly (for debugging)

```bash
python3 run.py
```

### 3. Run as a systemd service (start on boot)

Create `/etc/systemd/system/lcd-cpu-temp.service`:

```ini
[Unit]
Description=NZXT Kraken LCD Temperature Display
After=systemd-udev-settle.service

[Service]
User=your-username
ExecStartPre=/usr/bin/udevadm settle --timeout=30
ExecStart=/usr/bin/python3 /path/to/run.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lcd-cpu-temp
```

Common commands:

```bash
sudo systemctl start lcd-cpu-temp    # Start
sudo systemctl stop lcd-cpu-temp     # Stop
sudo systemctl restart lcd-cpu-temp  # Restart
journalctl -u lcd-cpu-temp -f        # Follow live logs
liquidctl status                     # Show device temps and fan speeds
```

## Fan Control

Fan speed is adjusted automatically based on a **moving average of coolant temperature** (3 samples, 6-second smoothing):

| Coolant temp | Fan duty |
|-------------|---------|
| < 32°C | 35% |
| 32°C | 35% |
| 35°C | 50% |
| 40°C | 75% |
| ≥ 45°C | 100% |

Values between points are linearly interpolated. A 3% deadband prevents unnecessary writes.

The pump runs at a fixed 100% and is maintained autonomously by the firmware after the initial write.

To adjust behavior, edit the constants at the top of `cooler/fan_liquid.py`: `CURVE`, `MIN_DUTY`, `WINDOW`, `DEADBAND`.

## Layout Customization

All layout parameters are top-level constants in `screen/render.py`. Edit and restart the service to apply:

- **Dividers**: `DIVX` `DIVY` `LINE_Y_TOP` `LINE_Y_BOT` `LINE_X_END`
- **Arc progress bar**: `ARC_MARGIN` `ARC_START` `ARC_SWEEP` `ARC_WIDTH`
- **Font sizes**: `FONT_CPU` `FONT_CPU_DEG` `FONT_CPU_LBL` `FONT_SM` `FONT_SM_DEG` `FONT_SM_LBL` `FONT_LINUX`
- **Number centers**: `CPU_NUM_CX/CY` `LIQ_NUM_CX/CY` `GPU_NUM_CX/CY`
- **Label positions**: `CPU_LBL_CX/CY` `LIQ_LBL_CX/CY` `GPU_LBL_CX/CY`

## Notes

- On service stop, the display automatically reverts to the device's built-in coolant temperature mode and all LCD buckets are cleaned up
- GPU temperature is read directly via NVML without invoking `nvidia-smi`; if GPU reading fails, the display continues showing CPU and coolant temperatures normally
- Pump/fan settings are stored in device non-volatile memory and survive reboots; the service still rewrites them on startup to ensure expected values

## License

This project is licensed under **GPL-3.0-or-later**.

`screen/_set_screen_local.py` is derived from [liquidctl](https://github.com/liquidctl/liquidctl) (LGPL-3.0). In accordance with the terms of LGPL-3.0, this project as a whole is released under the compatible GPL-3.0 license. See the [LICENSE](LICENSE) file for details.
