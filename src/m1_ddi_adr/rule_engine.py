import sqlite3
from typing import List, Dict, Optional
from ..cdss_core.log_lr import LogLikelihoodRatio

class DDIRuleEngine:
    """Rule-based DDI detection from curated knowledge base (FDA, DrugBank)."""

    def __init__(self, db_path="database/rezpharma.db"):
        self.db_path = db_path

    def check_interactions(self, drug_list: List[str]) -> List[Dict]:
        interactions = []
        for i, perp in enumerate(drug_list):
            for vict in drug_list[i+1:]:
                hit = self._query(perp, vict)
                if hit:
                    interactions.append(hit)
        return interactions

    def _query(self, perpetrator, victim) -> Optional[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT mechanism, severity, log_lr, evidence_level "
                "FROM ddi_interactions d "
                "JOIN drugs p ON d.perpetrator_drug_id = p.drug_id "
                "JOIN drugs v ON d.victim_drug_id = v.drug_id "
                "WHERE p.generic_name=? AND v.generic_name=?",
                (perpetrator, victim))
            row = cur.fetchone()
            conn.close()
            if row:
                return {
                    "perpetrator": perpetrator, "victim": victim,
                    "mechanism": row[0], "severity": row[1],
                    "log_lr": row[2], "evidence_level": row[3],
                    "provenance_id": f"m1_rule_{perpetrator}_{victim}"
                }
        except Exception:
            pass
        return None

    def to_log_lr(self, interaction: Dict) -> LogLikelihoodRatio:
        return LogLikelihoodRatio(
            value=interaction["log_lr"],
            provenance_id=interaction["provenance_id"],
            module="M1",
            mechanism=interaction["mechanism"],
            evidence_level=interaction["evidence_level"])
