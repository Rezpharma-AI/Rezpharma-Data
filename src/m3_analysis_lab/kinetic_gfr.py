
import numpy as np
from scipy.stats import norm
from ..cdss_core.particles import ParticleSet

class KineticGFR:
    def __init__(self, n_particles=1000):
        self.n_particles = n_particles

    def estimate(self, creatinine_series, muscle_mass=1.1, weight=80):
        # Generation rate G (mg/day) approx 20 * weight
        G = 20 * weight 
        # Volume V (L) approx 0.6 * weight
        V = 0.6 * weight 
        
        particles = np.random.normal(90, 20, self.n_particles)
        particles = np.clip(particles, 5, 200)
        weights = np.ones(self.n_particles) / self.n_particles
        
        if len(creatinine_series) < 2:
            return ParticleSet(particles, weights)
            
        for i in range(1, len(creatinine_series)):
            t_prev, c_prev = creatinine_series[i-1]
            t_curr, c_curr = creatinine_series[i]
            dt = max(t_curr - t_prev, 1.0)
            
            # Predict: Random walk
            particles += np.random.normal(0, 3, self.n_particles)
            particles = np.clip(particles, 5, 200)
            
            c_avg = (c_prev + c_curr) / 2
            dc_dt = (c_curr - c_prev) / dt
            G_hr = G / 24.0
            V_dL = V * 10.0
            
            # Kinetic GFR mass balance denominator
            denominator = 1 + (dc_dt * V_dL / G_hr)
            if denominator <= 0.1: denominator = 0.1
            
            expected_gfr = (G_hr / c_avg) * (1.0 / denominator) * 100
            expected_gfr = np.clip(expected_gfr, 5, 200)
            
            # Update particles based on likelihood
            likelihoods = norm.pdf(expected_gfr, loc=particles, scale=15)
            weights *= likelihoods + 1e-300
            weights /= np.sum(weights)
            
            # Resample
            ess = 1.0 / np.sum(weights**2)
            if ess < self.n_particles / 2:
                positions = (np.random.random() + np.arange(self.n_particles)) / self.n_particles
                cumsum = np.cumsum(weights)
                indices = np.searchsorted(cumsum, positions)
                particles = particles[np.clip(indices, 0, self.n_particles-1)]
                weights = np.ones(self.n_particles) / self.n_particles
                
        return ParticleSet(particles, weights)
