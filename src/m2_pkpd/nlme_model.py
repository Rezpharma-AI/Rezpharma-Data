import numpy as np
from dataclasses import dataclass

@dataclass
class PKParameters:
    cl: float
    v: float
    ka: float
    f_bio: float

class NLMEModel:
    """Population PK model with allometric scaling and covariates."""

    def __init__(self, drug_name, pop_params=None):
        self.drug_name = drug_name
        self.pop_params = pop_params or {
            "cl_pop": 10.0, "v_pop": 50.0, "ka_pop": 1.5,
            "f_bio": 0.8, "theta_gfr": 0.75,
            "omega_cl": 0.3, "omega_v": 0.2}

    def predict_parameters(self, weight, gfr, age=50):
        p = self.pop_params
        cl = p["cl_pop"] * (weight / 70.0) ** 0.75
        v = p["v_pop"] * (weight / 70.0) ** 1.0
        cl *= (gfr / 90.0) ** p["theta_gfr"]
        if age > 65:
            cl *= 0.85
        return PKParameters(cl=cl, v=v, ka=p["ka_pop"], f_bio=p["f_bio"])

    def predict_concentration(self, params, dose, time):
        ke = params.cl / params.v
        if abs(params.ka - ke) < 1e-10:
            c = (params.f_bio * dose * params.ka / params.v) * time * np.exp(-ke * time)
        else:
            c = (params.f_bio * dose * params.ka /
                 (params.v * (params.ka - ke))) * (np.exp(-ke * time) - np.exp(-params.ka * time))
        return max(c, 0.0)
