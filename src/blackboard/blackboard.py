from datetime import datetime
from typing import Dict, Any, List, Optional
from ..cdss_core.distributions import NormalPosterior
from ..cdss_core.fusion import precision_weighted_fusion
from ..cdss_core.log_lr import LogLikelihoodRatio
import numpy as np

class ProvenanceError(Exception):
    """Raised when duplicate evidence is detected (echo prevention)."""
    pass

class Blackboard:
    """Joint posterior maintenance with strict provenance tracking."""

    def __init__(self, patient_id="unknown"):
        self.patient_id = patient_id
        self.latent_states: Dict[str, Any] = {}
        self.harm_log_lrs: Dict[str, List[LogLikelihoodRatio]] = {}
        self.provenance: set = set()
        self.audit_log: List[Dict] = []

    def update_latent(self, latent_id, evidence, provenance_id, module):
        if provenance_id in self.provenance:
            raise ProvenanceError(
                f"Duplicate evidence: {provenance_id} from {module}. Echo prevented.")
        self.provenance.add(provenance_id)
        if latent_id in self.latent_states:
            existing = self.latent_states[latent_id]
            if isinstance(existing, NormalPosterior) and isinstance(evidence, NormalPosterior):
                self.latent_states[latent_id] = precision_weighted_fusion([existing, evidence])
            else:
                self.latent_states[latent_id] = evidence
        else:
            self.latent_states[latent_id] = evidence
        self.audit_log.append({"ts": datetime.now().isoformat(),
                               "action": "update_latent", "latent": latent_id,
                               "module": module, "provenance": provenance_id})

    def add_harm_evidence(self, harm_id, log_lr: LogLikelihoodRatio):
        if log_lr.provenance_id in self.provenance:
            raise ProvenanceError(f"Duplicate harm evidence: {log_lr.provenance_id}")
        self.provenance.add(log_lr.provenance_id)
        self.harm_log_lrs.setdefault(harm_id, []).append(log_lr)
        self.audit_log.append({"ts": datetime.now().isoformat(),
                               "action": "add_harm", "harm": harm_id,
                               "module": log_lr.module, "log_lr": log_lr.value})

    def get_latent(self, latent_id):
        return self.latent_states.get(latent_id)

    def get_fused_log_lr(self, harm_id):
        return sum(lr.value for lr in self.harm_log_lrs.get(harm_id, []))

    def get_posterior_probability(self, harm_id, prior_prob=0.05):
        fused = self.get_fused_log_lr(harm_id)
        prior_odds = prior_prob / (1 - prior_prob)
        post_odds = prior_odds * np.exp(fused)
        return float(post_odds / (1 + post_odds))

    def get_full_state(self):
        return {"patient_id": self.patient_id,
                "latent_states": {k: str(v) for k, v in self.latent_states.items()},
                "harm_propositions": {h: {"fused_lr": self.get_fused_log_lr(h),
                                          "posterior_p": self.get_posterior_probability(h)}
                                      for h in self.harm_log_lrs},
                "total_evidence": len(self.provenance)}
