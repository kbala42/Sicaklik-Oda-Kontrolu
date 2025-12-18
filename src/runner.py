import numpy as np
from dataclasses import dataclass
from .model import discretize_2rc
from .kalman import Kalman
from .pid import PID
from .mpc_lite import mpc_lite_control
from .metrics import compute_metrics

@dataclass
class Scenario:
    name: str
    Ta: float
    mismatch: str
    profile: str

def profile_step(T0, Tstep, total_steps):
    return np.full(total_steps, Tstep, dtype=float)

def profile_ramp(T0, Tend, duration_steps, total_steps):
    r = np.full(total_steps, Tend, dtype=float)
    slope = (Tend - T0) / max(1, duration_steps)
    for k in range(min(duration_steps, total_steps)):
        r[k] = T0 + slope * k
    return r

def profile_multistep(T0, mids, durations, total_steps):
    r = np.full(total_steps, T0, dtype=float)
    t = 0; current = T0
    for target, dur in zip(mids, durations):
        for i in range(dur):
            if t >= total_steps: break
            inc = (target - current) / max(1, dur)
            r[t] = current + inc * i
            t += 1
        current = target
        if t >= total_steps: break
    if t < total_steps: r[t:] = current
    return r

def run_scenario(scn: Scenario, controller_type="PID", Ts=1.0, sim_seconds=300,
                 params_nominal=None, T_max=65.0, seed=42, mpc_cfg=None, pid_cfg=None):
    np.random.seed(seed)
    steps = int(sim_seconds / Ts)
    if params_nominal is None:
        params_nominal = dict(Cr=1500.0, Cs=300.0, Rrs=1.2, Rra=4.0, alpha=50.0)

    mult = 1.0
    if scn.mismatch == "minus20": mult = 0.8
    if scn.mismatch == "plus20":  mult = 1.2

    params_plant = dict(
        Cr=params_nominal["Cr"]*mult,
        Cs=params_nominal["Cs"]*mult,
        Rrs=params_nominal["Rrs"]*mult,
        Rra=params_nominal["Rra"]*mult,
        alpha=params_nominal["alpha"]
    )
    Ad_p, Bd_p, Ed_p, C = discretize_2rc(**params_plant, Ts=Ts)
    Ad_m, Bd_m, Ed_m, C_m = discretize_2rc(**params_nominal, Ts=Ts)

    T0 = 25.0
    if scn.profile == "step":
        r = profile_step(T0, 60.0, steps)
    elif scn.profile == "ramp":
        r = profile_ramp(T0, 60.0, duration_steps=int(0.6*steps), total_steps=steps)
    else:
        r = profile_multistep(40.0, [55.0, 45.0], [int(0.4*steps), int(0.4*steps)], steps)

    x = np.array([[T0],[T0]], dtype=float)
    y = np.zeros(steps, dtype=float)
    u = np.zeros(steps, dtype=float)
    sigma_y = 0.2

    kf = Kalman(Ad_m, Bd_m, Ed_m, C_m, Q_scale=1e-4, R_var=sigma_y**2)

    if pid_cfg is None:
        pid_cfg = dict(kp=0.9, ki=0.03, kd=0.08, umin=0.0, umax=1.0, du_max=0.06)
    pid = PID(Ts=Ts, **pid_cfg)

    if mpc_cfg is None:
        mpc_cfg = dict(N=8, qy=1.0, qdu=0.08, umin=0.0, umax=1.0, du_max=0.06, Ta=scn.Ta)

    x_est = np.array([[T0],[T0]], dtype=float)
    u_prev = 0.0

    for k in range(steps):
        yk = float(C @ x) + np.random.randn()*sigma_y
        kf.update(np.array([[yk]]))
        x_est = kf.x.copy()

        if controller_type == "PID":
            uk = pid.step(r[k], yk)
        else:
            r_seq = np.full(mpc_cfg["N"], r[k])
            uk = mpc_lite_control(Ad_m, Bd_m, C_m, x_est, r_seq, mpc_cfg["N"], u_prev,
                                  mpc_cfg["umin"], mpc_cfg["umax"], mpc_cfg["du_max"],
                                  mpc_cfg["qy"], mpc_cfg["qdu"], Ta=scn.Ta, Ed=Ed_m,
                                  max_iter=6, step=0.08)
        u[k] = uk
        y[k] = float(C @ x)
        x = Ad_p @ x + Bd_p * uk + Ed_p * scn.Ta
        kf.predict(uk, scn.Ta)
        u_prev = uk

    m = compute_metrics(y, r, u, T_max=T_max, Ts=Ts)
    return m, dict(y=y, r=r, u=u)
