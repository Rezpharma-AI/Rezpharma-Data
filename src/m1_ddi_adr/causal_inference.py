import numpy as np
from ..cdss_core.log_lr import LogLikelihoodRatio

class SCCSValidator:
    """Self-Controlled Case Series for causal validation."""

    def __init__(self, risk_window_days=28):
        self.risk_window_days = risk_window_days

    def validate_signal(self, events_in_risk, events_in_control,
                        risk_time, control_time):
        if control_time == 0 or risk_time == 0:
            return 0.0, 1.0
        rate_risk = events_in_risk / risk_time
        rate_control = events_in_control / control_time
        if rate_control == 0:
            return 0.0, 1.0
        ri = rate_risk / rate_control
        log_lr = np.log(ri) if ri > 0 else 0.0
        from scipy.stats import poisson
        expected = rate_control * risk_time
        p_val = 1 - poisson.cdf(events_in_risk, expected) if expected > 0 else 1.0
        return log_lr, p_val

    def to_log_lr(self, log_lr, p_value, provenance_id):
        level = "sccs_confirmed" if p_value < 0.05 else "signal"
        return LogLikelihoodRatio(
            value=log_lr, provenance_id=provenance_id,
            module="M1", mechanism="SCCS", evidence_level=level)
