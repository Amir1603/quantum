from .h1 import H1_B
from .v import V_B
from .charge import Charge
from .current import Current
from .bobs_energy import BobsEnergy
from .observable import Observable
from Calculators.tfim_calculator import TFIMCalculator
from conf import Conf
import utils

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ObservableFactory(metaclass=Singleton):
    def create_observables(self, conf: Conf, calc: TFIMCalculator) -> tuple[list[Observable], list[Observable]]:
        indices = [utils.get_charlie_idx(conf.N), utils.get_bob_idx(conf.N)]
        obs = []
        derived_obs = []

        for idx in indices:
            obs.extend([H1_B(idx, conf, calc), V_B(idx, conf, calc), Charge(idx, conf, calc)])
            derived_obs.append(BobsEnergy(idx, conf, calc))

        return obs, derived_obs
