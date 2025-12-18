import numpy as np

def discretize_2rc(Cr, Cs, Rrs, Rra, alpha, Ts):
    A = np.array([
        [-(1/(Cr*Rra) + 1/(Cr*Rrs)),  1/(Cr*Rrs)],
        [ 1/(Cs*Rrs),                -(1/(Cs*Rrs))]
    ], dtype=float)
    B = np.array([[alpha/Cr],[0.0]], dtype=float)
    E = np.array([[1/(Cr*Rra)],[0.0]], dtype=float)
    Ad = np.eye(2) + Ts * A
    Bd = Ts * B
    Ed = Ts * E
    C = np.array([[1.0, 0.0]], dtype=float)
    return Ad, Bd, Ed, C
