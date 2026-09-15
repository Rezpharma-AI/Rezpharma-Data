import numpy as np
from scipy.optimize import minimize_scalar

class ModelCalibrator:
    """Temperature scaling for local site calibration."""

    def __init__(self, t_min=0.1, t_max=10.0):
        self.t_min = t_min
        self.t_max = t_max
        self.temperature = 1.0

    def fit_temperature(self, logits, labels):
        def nll(T):
            probs = 1.0 / (1.0 + np.exp(-logits / T))
            probs = np.clip(probs, 1e-10, 1 - 1e-10)
            return -np.mean(labels * np.log(probs) + (1 - labels) * np.log(1 - probs))
        result = minimize_scalar(nll, bounds=(self.t_min, self.t_max), method="bounded")
        self.temperature = result.x
        return self.temperature

    def calibrate(self, logits):
        return 1.0 / (1.0 + np.exp(-logits / self.temperature))
