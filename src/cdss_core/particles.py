import numpy as np

class ParticleSet:
    """Weighted particle approximation of a posterior distribution."""

    def __init__(self, particles, weights=None):
        self.particles = np.asarray(particles, dtype=float)
        if weights is None:
            self.weights = np.ones(len(particles)) / len(particles)
        else:
            self.weights = np.asarray(weights, dtype=float)
            self.weights /= np.sum(self.weights)

    @property
    def n_particles(self):
        return len(self.particles)

    @property
    def effective_sample_size(self):
        return 1.0 / np.sum(self.weights ** 2)

    def mean(self):
        return np.average(self.particles, weights=self.weights)

    def variance(self):
        mu = self.mean()
        return np.average((self.particles - mu) ** 2, weights=self.weights)

    def std(self):
        return np.sqrt(self.variance())

    def quantile(self, q):
        idx = np.argsort(self.particles)
        cumw = np.cumsum(self.weights[idx])
        return self.particles[idx][np.searchsorted(cumw, q)]

    def credible_interval(self, level=0.95):
        alpha = (1 - level) / 2
        return (self.quantile(alpha), self.quantile(1 - alpha))

    def resample_systematic(self):
        positions = (np.random.random() + np.arange(self.n_particles)) / self.n_particles
        cumsum = np.cumsum(self.weights)
        indices = np.clip(np.searchsorted(cumsum, positions), 0, self.n_particles - 1)
        return ParticleSet(self.particles[indices].copy())

    def __repr__(self):
        return f"ParticleSet(n={self.n_particles}, mean={self.mean():.3f})"

    def to_normal_approximation(self):
        from .distributions import NormalPosterior
        return NormalPosterior(mu=self.mean(), sigma=self.std())
