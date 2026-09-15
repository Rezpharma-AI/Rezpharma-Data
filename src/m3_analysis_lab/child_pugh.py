import numpy as np

class ChildPughPosterior:
    """Posterior PMF over Child-Pugh classes A, B, C via Monte Carlo."""

    def __init__(self, n_samples=5000):
        self.n_samples = n_samples

    def compute(self, bilirubin, albumin, inr, ascites=1, enceph=1):
        bili_s = np.maximum(np.random.normal(bilirubin, 0.1 * bilirubin, self.n_samples), 0.1)
        alb_s = np.clip(np.random.normal(albumin, 0.1, self.n_samples), 0.5, 5.0)
        inr_s = np.maximum(np.random.normal(inr, 0.05 * inr, self.n_samples), 0.8)

        bs = np.ones_like(bili_s)
        bs[(bili_s >= 2) & (bili_s < 3)] = 2
        bs[bili_s >= 3] = 3

        als = np.ones_like(alb_s)
        als[(alb_s >= 2.8) & (alb_s < 3.5)] = 2
        als[alb_s < 2.8] = 3

        ins = np.ones_like(inr_s)
        ins[(inr_s >= 1.7) & (inr_s < 2.3)] = 2
        ins[inr_s >= 2.3] = 3

        total = bs + als + ins + ascites + enceph
        return {"A": float(np.mean(total <= 6)),
                "B": float(np.mean((total >= 7) & (total <= 9))),
                "C": float(np.mean(total >= 10))}
