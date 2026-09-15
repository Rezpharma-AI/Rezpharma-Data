from typing import List
from .distributions import NormalPosterior

def precision_weighted_fusion(posteriors: List[NormalPosterior]) -> NormalPosterior:
    """Fuse multiple NormalPosterior objects using precision weighting."""
    if not posteriors:
        raise ValueError("Cannot fuse empty list")
    total_prec = sum(p.precision for p in posteriors)
    fused_mu = sum(p.mu * p.precision for p in posteriors) / total_prec
    fused_sigma = (1.0 / total_prec) ** 0.5
    return NormalPosterior(mu=fused_mu, sigma=fused_sigma)
