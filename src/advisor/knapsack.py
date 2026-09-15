class AlertBudgetSelector:
    """Greedy knapsack selection under alert budget constraint."""

    def __init__(self, budget=3):
        self.budget = budget

    def select_alerts(self, alerts):
        sorted_alerts = sorted(alerts,
            key=lambda a: a.get("net_benefit", 0) / max(a.get("attention_cost", 1), 1e-6),
            reverse=True)
        selected, remaining = [], self.budget
        for alert in sorted_alerts:
            cost = alert.get("attention_cost", 1)
            if cost <= remaining:
                selected.append(alert)
                remaining -= cost
        return selected
