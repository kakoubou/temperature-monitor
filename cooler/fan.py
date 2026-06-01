from collections import deque

# 温度（°C）→ 占空比（%）曲线，线性插值
CURVE = [(30, 35), (50, 50), (60, 80), (70, 100)]
MIN_DUTY = 35  # 低于 CURVE[0] 温度时的固定值

# 移动平均窗口大小（× 主循环间隔 = 平滑时间，默认 2s×5=10s）
WINDOW = 3

# 触发实际写入的最小变化量（百分比点）
DEADBAND = 3


def _interpolate(temp: float) -> int:
    if temp < CURVE[0][0]:
        return MIN_DUTY
    if temp >= CURVE[-1][0]:
        return CURVE[-1][1]
    for (t0, d0), (t1, d1) in zip(CURVE, CURVE[1:]):
        if t0 <= temp <= t1:
            return round(d0 + (d1 - d0) * (temp - t0) / (t1 - t0))
    return CURVE[-1][1]


class FanController:
    def __init__(self):
        self._samples = deque(maxlen=WINDOW)
        self._duty: int | None = None

    def update(self, dev, cpu_temp: float) -> bool:
        """用当前 CPU 温度更新风扇转速，返回是否实际写入了新指令。"""
        self._samples.append(cpu_temp)
        avg = sum(self._samples) / len(self._samples)
        new_duty = _interpolate(avg)

        if self._duty is None or abs(new_duty - self._duty) >= DEADBAND:
            dev.set_fixed_speed("fan", new_duty)
            self._duty = new_duty
            return True
        return False

    @property
    def duty(self) -> int | None:
        return self._duty
