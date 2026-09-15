import numpy as np
from dataclasses import dataclass

@dataclass
class NormalPosterior:
    """Represents N(mu, sigma^2) for precision-weighted fusion."""
    mu: float
    sigma: float

    def __post_init__(self):
        if self.sigma <= 0:
            raise ValueError(f"sigma must be positive, got {self.sigma}")

    @property
    def precision(self) -> float:
        return 1.0 / (self.sigma ** 2)

    @property
    def variance(self) -> float:
        return self.sigma ** 2

    def credible_interval(self, level=0.95):
        from scipy.stats import norm
        z = norm.ppf((1 + level) / 2)
        return (self.mu - z * self.sigma, self.mu + z * self.sigma)

    def __repr__(self):
        return f"N(mu={self.mu:.3f}, sigma={self.sigma:.3f})"
