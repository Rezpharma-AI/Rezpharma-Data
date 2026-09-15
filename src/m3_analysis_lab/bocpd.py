import numpy as np
from scipy.stats import norm

class BOCPDDetector:
    """Bayesian Online Change-Point Detection (Adams and MacKay 2007)."""

    def __init__(self, hazard_prob=0.01, obs_noise=1.0):
        self.hazard_prob = hazard_prob
        self.obs_noise = obs_noise
        self.run_length_probs = np.array([1.0])
        self.data = []

    def update(self, new_observation):
        self.data.append(new_observation)
        t = len(self.data)
        predictive_probs = np.zeros(len(self.run_length_probs) + 1)
        for r in range(len(self.run_length_probs)):
            segment = self.data[max(0, t - r - 1):t]
            mu = np.mean(segment) if len(segment) > 0 else new_observation
            sigma = max(np.std(segment), self.obs_noise) if len(segment) > 1 else self.obs_noise
            predictive_probs[r] = norm.pdf(new_observation, mu, sigma)
        growth = predictive_probs[:-1] * self.run_length_probs * (1 - self.hazard_prob)
        change = np.sum(predictive_probs[:-1] * self.run_length_probs * self.hazard_prob)
        new_rl = np.zeros(len(self.run_length_probs) + 1)
        new_rl[0] = change
        new_rl[1:] = growth
        total = np.sum(new_rl)
        self.run_length_probs = new_rl / total if total > 0 else np.ones_like(new_rl) / len(new_rl)
        return float(self.run_length_probs[0])
