from dataclasses import dataclass

@dataclass
class Action:
    name: str
    utility_if_harm: float
    utility_if_no_harm: float
    attention_cost: int = 1

class ExpectedUtilityCalculator:
    """Selects optimal actions based on expected utility theory."""

    def __init__(self):
        self.actions = []

    def add_action(self, name, u_harm, u_noharm, cost=1):
        self.actions.append(Action(name, u_harm, u_noharm, cost))

    def calculate_eu(self, action, p_harm):
        return p_harm * action.utility_if_harm + (1 - p_harm) * action.utility_if_no_harm

    def select_best_action(self, p_harm):
        if not self.actions:
            return {"selected": None}
        eu_values = {a.name: self.calculate_eu(a, p_harm) for a in self.actions}
        best = max(self.actions, key=lambda a: eu_values[a.name])
        return {"selected": best.name, "expected_utility": eu_values[best.name],
                "all_eu_values": eu_values}
