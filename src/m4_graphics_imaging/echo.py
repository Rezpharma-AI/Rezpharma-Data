import numpy as np

class EchoCovariateExtractor:
    """Extracts EF and fluid status with modality-specific error models."""
    ECHO_EF_VARIANCE = 25.0
    POCUS_EF_VARIANCE = 49.0

    def extract_ef(self, ef_reported, modality="echo"):
        var = self.ECHO_EF_VARIANCE if modality == "echo" else self.POCUS_EF_VARIANCE
        return {"ef_mean": ef_reported, "ef_variance": var,
                "ef_std": np.sqrt(var), "modality": modality}

    def extract_fluid_status(self, ivc_diameter_cm, ivc_collapsibility):
        logit = -3.0 + 1.5 * ivc_diameter_cm - 2.0 * ivc_collapsibility
        return {"p_fluid_overload": 1.0 / (1.0 + np.exp(-logit))}
