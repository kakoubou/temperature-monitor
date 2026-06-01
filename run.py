#!/usr/bin/env python3
import sys, time, signal

_TTY = sys.stdout.isatty()
import liquidctl
from screen import make_image
from screen._set_screen_local import set_screen_local
from sensor import get_cpu_temp, get_gpu_temp, get_liquid_temp
from cooler import apply_pump_speed, FanController

INTERVAL = 1

running = True

def handle_signal(sig, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

devices = list(liquidctl.find_liquidctl_devices(match="Kraken"))
if not devices:
    print("ERROR: 未找到 Kraken 设备", file=sys.stderr)
    sys.exit(1)

dev = devices[0]
print(f"设备: {dev.description}")

with dev.connect():
    dev.initialize()
    apply_pump_speed(dev)
    fan_ctrl = FanController()
    dev._switch_bucket(0, 2)
    buckets = dev._query_buckets()
    for i, b in buckets.items():
        if any(b[15:]):
            dev._delete_bucket(i)
    print("已清空残留 bucket")
    print(f"开始每 {INTERVAL} 秒更新 LCD...")

    while running:
        cpu_temp    = get_cpu_temp()
        liquid_temp = get_liquid_temp(dev)
        gpu_temp    = get_gpu_temp()

        if cpu_temp    is None: print("[WARN] CPU 温度读取失败")
        if liquid_temp is None: print("[WARN] 液温读取失败")

        if cpu_temp is not None and liquid_temp is not None:
            fan_ctrl.update(dev, liquid_temp)
            img = make_image(cpu_temp, liquid_temp, gpu_temp)
            raw = img.tobytes()
            data = [v for i in range(0, len(raw), 3) for v in (raw[i], raw[i+1], raw[i+2], 0)]
            set_screen_local(dev, "lcd", "static", data)
            end = "\r" if _TTY else "\n"
            print(f"{time.strftime('%H:%M:%S')} "
                  f"CPU:{cpu_temp:.1f}  LIQ:{liquid_temp}  GPU:{gpu_temp}"
                  f"  FAN:{fan_ctrl.duty}%",
                  end=end, flush=True)
        time.sleep(INTERVAL)

    # 停止时清理：切回液冷内置模式，删除所有 bucket，删除临时图片
    dev._switch_bucket(0, 2)
    buckets = dev._query_buckets()
    for i, b in buckets.items():
        if any(b[15:]):
            dev._delete_bucket(i)
    print("\n已清理，停止")
