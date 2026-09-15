import numpy as np
from dataclasses import dataclass

@dataclass
class SignalResult:
    drug: str
    event: str
    n_observed: int
    e_expected: float
    ebgm: float
    ebgm_lower: float
    is_signal: bool

class EBGMSignalMiner:
    """DuMouchel gamma-Poisson shrinkage (MGPS) for FAERS signal detection."""

    def __init__(self, alpha=0.2, beta=0.1, signal_threshold=2.0):
        self.alpha = alpha
        self.beta = beta
        self.signal_threshold = signal_threshold

    def compute_ebgm(self, n_observed: int, e_expected: float) -> float:
        return (self.alpha + n_observed) / (self.beta + e_expected)

    def detect_signal(self, drug, event, n_observed, e_expected) -> SignalResult:
        from scipy.stats import gamma as gamma_dist
        ebgm = self.compute_ebgm(n_observed, e_expected)
        post_alpha = self.alpha + n_observed
        post_beta = self.beta + e_expected
        ebgm_lower = gamma_dist.ppf(0.05, post_alpha, scale=1.0 / post_beta)
        return SignalResult(
            drug=drug, event=event, n_observed=n_observed,
            e_expected=e_expected, ebgm=ebgm, ebgm_lower=ebgm_lower,
            is_signal=(ebgm_lower > self.signal_threshold))
