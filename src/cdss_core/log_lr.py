import numpy as np
from dataclasses import dataclass
from typing import List

@dataclass
class LogLikelihoodRatio:
    """Encapsulates a log-LR contribution from a single module."""
    value: float
    provenance_id: str
    module: str
    mechanism: str = ""
    evidence_level: str = "curated"

def fuse_log_lrs(log_lrs: List[LogLikelihoodRatio]) -> float:
    """Additive fusion of independent log-LRs."""
    return sum(lr.value for lr in log_lrs)

def log_lr_to_posterior_prob(log_lr: float, prior_prob: float = 0.05) -> float:
    """Convert log-LR to posterior probability via Bayes rule."""
    prior_odds = prior_prob / (1 - prior_prob)
    log_post_odds = np.log(prior_odds) + log_lr
    post_odds = np.exp(log_post_odds)
    return post_odds / (1 + post_odds)
