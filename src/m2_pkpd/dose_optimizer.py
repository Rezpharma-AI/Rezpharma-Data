import numpy as np

class ChanceConstrainedOptimizer:
    """Chance-constrained dosing: P(AUC>target)>0.90, P(Cmax>tox)<0.10."""

    def __init__(self, target_attainment=0.90, toxicity_ceiling=0.10):
        self.target_attainment = target_attainment
        self.toxicity_ceiling = toxicity_ceiling

    def optimize(self, posterior_samples, target_auc, tox_cmax, dose_grid=None):
        if dose_grid is None:
            dose_grid = np.arange(100, 5001, 100)
        best_dose, best_prob, p_tox = dose_grid[0], 0.0, 0.0
        for dose in dose_grid:
            aucs = dose / posterior_samples[:, 0]
            cmaxs = dose / posterior_samples[:, 1]
            p_att = np.mean(aucs > target_auc)
            p_tox = np.mean(cmaxs > tox_cmax)
            if p_att >= self.target_attainment and p_tox <= self.toxicity_ceiling:
                return {"recommended_dose": dose, "p_target_attainment": p_att,
                        "p_toxicity": p_tox, "n_posterior_samples": len(posterior_samples)}
            if p_att > best_prob:
                best_dose, best_prob = dose, p_att
        return {"recommended_dose": best_dose, "p_target_attainment": best_prob,
                "p_toxicity": p_tox, "n_posterior_samples": len(posterior_samples)}
