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
    def create_observables(self, conf: Conf, calc: TFIMCalculator, sys: utils.System, alice_basis: utils.AliceBase = utils.AliceBase.X) -> tuple[list[Observable], list[Observable]]:
        v = V_B(conf, alice_basis, calc, sys)

        obs = [H1_B(conf, alice_basis, calc), v, Charge(conf, alice_basis, calc)]
        derived_obs = [BobsEnergy(conf, alice_basis, calc)]

        return obs, derived_obs
