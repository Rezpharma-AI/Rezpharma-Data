import numpy as np

class CTBodyComposition:
    """Body composition extraction for allometric PK scaling."""
    LEAN_MASS_VARIANCE = 4.0

    def segment(self, ct_scan_id, lean_mass_kg, visceral_fat_cm2):
        return {"lean_mass_kg": lean_mass_kg,
                "lean_mass_variance": self.LEAN_MASS_VARIANCE,
                "visceral_fat_cm2": visceral_fat_cm2,
                "allometric_factor_cl": (lean_mass_kg / 55.0) ** 0.75,
                "allometric_factor_v": (lean_mass_kg / 55.0) ** 1.0}
