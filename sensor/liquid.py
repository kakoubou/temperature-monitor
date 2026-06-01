def get_liquid_temp(dev):
    try:
        for key, val, _ in dev.get_status():
            if "Liquid temperature" in key:
                return float(val)
    except Exception:
        pass
    return None
