import numpy as np

def mpc_lite_control(Ad, Bd, C, x_est, r_seq, N, u_prev, umin, umax, du_max, qy, qdu, Ta=25.0, Ed=None, max_iter=6, step=0.08):
    nx = Ad.shape[0]
    U = np.full(N, float(u_prev))

    G = np.zeros((N, N))
    A_pow = np.eye(nx)
    for i in range(N):
        A_pow = Ad @ A_pow if i>0 else Ad
        Gi = (C @ A_pow @ Bd).item()
        for k in range(i, N):
            G[k, k-i] += Gi

    x = x_est.copy()
    y_free = np.zeros(N)
    for k in range(N):
        x = Ad @ x + (Ed * Ta if Ed is not None else 0.0)
        y_free[k] = float(C @ x)

    I = np.eye(N)
    D = I - np.eye(N, k=1); D[-1,-1]=1.0

    for _ in range(max_iter):
        Y = y_free + G @ U
        e = Y - r_seq
        grad = 2*qy * (G.T @ e) + 2*qdu * (D.T @ (D @ U - np.r_[U[0]-u_prev, np.diff(U)]))
        U = U - step * grad
        U = np.clip(U, umin, umax)
        U[0] = float(np.clip(U[0], u_prev - du_max, u_prev + du_max))
        for k in range(1, N):
            U[k] = float(np.clip(U[k], U[k-1] - du_max, U[k-1] + du_max))
    return float(U[0])
