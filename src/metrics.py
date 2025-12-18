import numpy as np

def compute_metrics(y, r, u, T_max=None, Ts=1.0):
    e = r - y
    iae = float(np.sum(np.abs(e)))
    ise = float(np.sum(e**2))
    r_final = r[-1]; y0 = y[0]
    denom = (r_final - y0) if abs(r_final - y0) > 1e-6 else 1.0
    overshoot = float(max(0.0, (np.max(y) - r_final) / denom * 100.0))
    band = 0.02 * max(1.0, abs(r_final))
    ts_idx = None
    for k in range(len(y)):
        if np.all(np.abs(y[k:] - r_final) <= band):
            ts_idx = k; break
    ts = float(ts_idx) * Ts if ts_idx is not None else float(len(y)*Ts)
    energy = float(np.sum(u**2))
    violation_time = 0.0
    if T_max is not None:
        violation_time = float(np.sum((y > T_max).astype(float)) * Ts)
    return {
        "IAE": iae,
        "ISE": ise,
        "Overshoot_%": overshoot,
        "Settling_s": ts,
        "Energy_sum_u2": energy,
        "Violation_s": violation_time
    }
