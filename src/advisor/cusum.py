class CUSUMMonitor:
    """Cumulative Sum chart for calibration drift detection."""

    def __init__(self, threshold=5.0, slack=0.5):
        self.threshold = threshold
        self.slack = slack
        self.s_pos = 0.0
        self.s_neg = 0.0
        self.alarm_count = 0

    def update(self, residual):
        self.s_pos = max(0, self.s_pos + residual - self.slack)
        self.s_neg = max(0, self.s_neg - residual - self.slack)
        alarm = self.s_pos > self.threshold or self.s_neg > self.threshold
        if alarm:
            self.alarm_count += 1
        return alarm

    def reset(self):
        self.s_pos = self.s_neg = 0.0
        self.alarm_count = 0
