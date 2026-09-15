import numpy as np

class RCVGate:
    """Reference Change Value gating based on biological variation (EFLM)."""

    BIOLOGICAL_VARIATION = {
        "creatinine": {"cv_a": 2.2, "cv_i": 6.0},
        "potassium": {"cv_a": 1.5, "cv_i": 4.8},
        "sodium": {"cv_a": 0.7, "cv_i": 0.7},
        "albumin": {"cv_a": 1.6, "cv_i": 3.1},
        "bilirubin": {"cv_a": 3.0, "cv_i": 26.0},
        "inr": {"cv_a": 2.0, "cv_i": 5.0},
        "alt": {"cv_a": 3.5, "cv_i": 18.0},
        "ast": {"cv_a": 3.0, "cv_i": 12.0},
    }

    def __init__(self, z_score=2.77):
        self.z_score = z_score

    def compute_rcv(self, analyte):
        bv = self.BIOLOGICAL_VARIATION.get(analyte, {"cv_a": 2.0, "cv_i": 5.0})
        return self.z_score * np.sqrt((bv["cv_a"] / 100) ** 2 + (bv["cv_i"] / 100) ** 2)

    def is_significant(self, prev, curr, analyte):
        if prev == 0:
            return True
        return abs(curr - prev) / prev > self.compute_rcv(analyte)
