from .tfim_calculator import TFIMCalculator
import numpy as np

class AnalyticalTFIM(TFIMCalculator):
    def __init__(self, N, J, h):
        if N != 2:
            raise ValueError("AnalyticalTFIM only supports N=2")

        super().__init__(N, J, h)

    def calc_all(self):
        self.E0 = None
        self.gs0 = None
        self.E1 = None
        self.ex1 = None
        self.gs_rho = None
        self.ex1_rho = None
        self.total_energy = None
        self.total_charge = None
        self.bob_energy = None
        self.bob_charge = 0.5 * (1.0 - self.h / np.sqrt(self.h**2 + self.k**2))
        self.theta_E1 = np.arcsin(
                (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
            ) / 2
        self.theta_q1 = np.arcsin(
                (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
            ) / 2

        # FIXME: Add when handling Alice basis choosing
        self.theta_E2 = None
        self.theta_q2 = None