import glob

_tctl_path = None

def _find_tctl():
    for hwmon in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        try:
            with open(f"{hwmon}/name") as f:
                if f.read().strip() != "k10temp":
                    continue
            for label_f in glob.glob(f"{hwmon}/temp*_label"):
                with open(label_f) as f:
                    if f.read().strip() == "Tctl":
                        return label_f.replace("_label", "_input")
        except OSError:
            continue
    return None

def get_cpu_temp():
    global _tctl_path
    try:
        if _tctl_path is None:
            _tctl_path = _find_tctl()
        if _tctl_path:
            with open(_tctl_path) as f:
                return int(f.read().strip()) / 1000.0
    except Exception:
        _tctl_path = None
    return None
