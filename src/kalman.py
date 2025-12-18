import numpy as np

class Kalman:
    def __init__(self, Ad, Bd, Ed, C, Q_scale=1e-4, R_var=0.04):
        nx = Ad.shape[0]
        self.Ad, self.Bd, self.Ed, self.C = Ad, Bd, Ed, C
        self.Q = Q_scale * np.eye(nx)
        self.R = np.array([[R_var]], dtype=float)
        self.x = np.zeros((nx,1), dtype=float)
        self.P = np.eye(nx, dtype=float)

    def predict(self, u, Ta):
        self.x = self.Ad @ self.x + self.Bd * u + self.Ed * Ta
        self.P = self.Ad @ self.P @ self.Ad.T + self.Q

    def update(self, y):
        S = self.C @ self.P @ self.C.T + self.R
        K = self.P @ self.C.T @ np.linalg.inv(S)
        self.x = self.x + K @ (y - self.C @ self.x)
        self.P = (np.eye(self.P.shape[0]) - K @ self.C) @ self.P
