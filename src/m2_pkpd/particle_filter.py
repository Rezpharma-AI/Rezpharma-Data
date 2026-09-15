import numpy as np
from scipy.stats import norm
from ..cdss_core.particles import ParticleSet

class ClearanceParticleFilter:
    """Bootstrap particle filter for non-stationary clearance (CL_t)."""

    def __init__(self, n_particles=1000, initial_cl=100.0,
                 process_noise=5.0, obs_noise=10.0):
        self.n_particles = n_particles
        self.process_noise = process_noise
        self.obs_noise = obs_noise
        self.particles = np.ones(n_particles) * initial_cl
        self.weights = np.ones(n_particles) / n_particles
        self.history = [self.particles.copy()]

    def predict(self, process_noise_std=None):
        q = process_noise_std or self.process_noise
        self.particles += np.random.normal(0, q, self.n_particles)
        self.particles = np.maximum(self.particles, 0.1)

    def update(self, observation, obs_noise_std=None):
        r = obs_noise_std or self.obs_noise
        likelihoods = norm.pdf(observation, loc=self.particles, scale=r)
        self.weights *= likelihoods
        self.weights += 1e-300
        self.weights /= np.sum(self.weights)

    def resample_if_needed(self, threshold=0.5):
        ess = 1.0 / np.sum(self.weights ** 2)
        if ess / self.n_particles < threshold:
            positions = (np.random.random() + np.arange(self.n_particles)) / self.n_particles
            cumsum = np.cumsum(self.weights)
            indices = np.clip(np.searchsorted(cumsum, positions), 0, self.n_particles - 1)
            self.particles = self.particles[indices].copy()
            self.weights = np.ones(self.n_particles) / self.n_particles

    def step(self, observation):
        self.predict()
        self.update(observation)
        self.resample_if_needed()
        self.history.append(self.particles.copy())

    def get_posterior(self):
        return ParticleSet(self.particles.copy(), self.weights.copy())

    def get_credible_band(self, level=0.95):
        return self.get_posterior().credible_interval(level)
