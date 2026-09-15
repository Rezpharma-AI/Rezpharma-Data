import numpy as np
from ..cdss_core.log_lr import LogLikelihoodRatio

class QTcRiskCalculator:
    """Conditional QT prolongation risk calculator."""
    TOXIC_THRESHOLD_MS = 500.0

    def calculate_risk(self, baseline_qtc, drug_liabilities,
                       potassium=None, magnesium=None):
        qt_eff = baseline_qtc + sum(drug_liabilities)
        if potassium is not None and potassium < 3.5:
            qt_eff += (3.5 - potassium) * 10
        if magnesium is not None and magnesium < 1.7:
            qt_eff += (1.7 - magnesium) * 15
        sigma_qt = 15.0
        from scipy.stats import norm
        p_toxic = 1 - norm.cdf(self.TOXIC_THRESHOLD_MS, loc=qt_eff, scale=sigma_qt)
        prior_p = 0.01
        if 0 < p_toxic < 1:
            log_lr = np.log(p_toxic / (1 - p_toxic)) - np.log(prior_p / (1 - prior_p))
        else:
            log_lr = 0.0
        return {"qt_effective_ms": qt_eff, "p_qtc_toxic": p_toxic, "log_lr": log_lr}
