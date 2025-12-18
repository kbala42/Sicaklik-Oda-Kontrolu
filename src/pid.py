import numpy as np

class PID:
    def __init__(self, kp, ki, kd, Ts, umin=0.0, umax=1.0, du_max=0.06):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.Ts = Ts
        self.umin, self.umax = umin, umax
        self.du_max = du_max
        self.e1 = 0.0
        self.e2 = 0.0
        self.u = 0.0

    def step(self, r, y):
        e = r - y
        du = self.kp*(e - self.e1) + self.ki*self.Ts*e + self.kd*(e - 2*self.e1 + self.e2)/self.Ts
        du = float(np.clip(du, -self.du_max, self.du_max))
        self.u = float(np.clip(self.u + du, self.umin, self.umax))
        self.e2, self.e1 = self.e1, e
        return self.u
