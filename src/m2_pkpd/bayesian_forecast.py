import numpy as np
from scipy.optimize import minimize
from .nlme_model import NLMEModel, PKParameters

class BayesianForecaster:
    """Bayesian MAP estimation from TDM data."""

    def __init__(self, model: NLMEModel):
        self.model = model

    def forecast(self, tdm_levels, prior_params, obs_noise=0.1):
        def neg_log_post(params_vec):
            cl, v = params_vec
            if cl <= 0 or v <= 0:
                return 1e10
            nll = 0.0
            for t, c_obs in tdm_levels:
                pk = PKParameters(cl=cl, v=v, ka=prior_params.ka, f_bio=prior_params.f_bio)
                c_pred = self.model.predict_concentration(pk, dose=1000, time=t)
                sigma = obs_noise * c_pred + 1e-6
                nll += 0.5 * ((c_obs - c_pred) / sigma) ** 2 + np.log(sigma)
            nll += 0.5 * (np.log(cl / prior_params.cl) / 0.3) ** 2
            nll += 0.5 * (np.log(v / prior_params.v) / 0.2) ** 2
            return nll

        x0 = [prior_params.cl, prior_params.v]
        result = minimize(neg_log_post, x0, method="Nelder-Mead", options={"maxiter": 1000})
        return {"map_cl": max(result.x[0], 0.01), "map_v": max(result.x[1], 0.1),
                "converged": result.success, "n_tdm_samples": len(tdm_levels)}
