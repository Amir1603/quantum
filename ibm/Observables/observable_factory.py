from .h1 import H1_B
from .v import V_B
from .charge import Charge
from .current import Current
from .bobs_energy import BobsEnergy
from .observable import Observable
from Calculators.tfim_calculator import TFIMCalculator
from conf import Conf


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ObservableFactory(metaclass=Singleton):
    def create_observables(self, conf: Conf, calc: TFIMCalculator) -> tuple[list[Observable], list[Observable]]:
        obs = [H1_B(conf, calc), V_B(conf, calc), Charge(conf, calc)]
        derived_obs = [BobsEnergy(conf, calc)]

        return obs, derived_obs
