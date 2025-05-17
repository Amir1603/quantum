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
    def __init__(self):
        self.derived_observables = []

    def create_observables(self, conf: Conf, calc: TFIMCalculator) -> list[Observable]:
        derived_obs = []
        obs_list: list[Observable] = []

        # FIXME: Figure out different Ns cases

        # Create instances of directly simulated observables
        if conf.N >= 3:
            print("Creating N>=3 observables (H1, V components + derived E_B + Charge_N)")
            obs_list.append(H1_B(conf, calc=calc))
            obs_list.append(V_B(conf, calc=calc))

            obs_list.append(Charge(conf, calc=calc))

        elif conf.N == 2:
            obs_list = [H1_B(conf, calc), V_B(conf, calc), Charge(conf, calc)]
            derived_obs.append(BobsEnergy(conf, calc))
        else:
            raise ValueError(f"Unsupported N={conf.N}")

        self.derived_observables.extend(derived_obs)

        return obs_list
