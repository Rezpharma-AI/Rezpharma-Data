import numpy as np

class DecisionCurveAnalysis:
    """Decision Curve Analysis for clinical utility evaluation."""

    def __init__(self, thresholds=None):
        self.thresholds = thresholds if thresholds is not None else np.linspace(0.01, 0.99, 99)

    def net_benefit(self, predictions, outcomes, threshold):
        n = len(predictions)
        if n == 0:
            return 0.0
        pred_pos = predictions >= threshold
        tp = np.sum(pred_pos & (outcomes == 1))
        fp = np.sum(pred_pos & (outcomes == 0))
        return (tp / n) - (fp / n) * (threshold / (1 - threshold))

    def compare_strategies(self, predictions, outcomes):
        nb_cdss = np.array([self.net_benefit(predictions, outcomes, t) for t in self.thresholds])
        prevalence = np.mean(outcomes)
        nb_all = prevalence - (1 - prevalence) * self.thresholds / (1 - self.thresholds)
        return {"thresholds": self.thresholds, "nb_cdss": nb_cdss,
                "nb_treat_all": nb_all, "nb_treat_none": np.zeros_like(self.thresholds)}
