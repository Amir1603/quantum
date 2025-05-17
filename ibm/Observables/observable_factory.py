from .h1 import H1_B
from .v import V_AB
from .charge import Charge
from .charge_n import Charge_N
from .current import Current
from .bobs_energy_n2 import BobsEnergy_N2
from .observable import Observable
from .h1_n import H1_N
from .v_n import V_N
from .bobs_energy_n import BobsEnergy_N
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

        # Create instances of directly simulated observables
        if conf.N >= 3:
            print("Creating N>=3 observables (H1, V components + derived E_B + Charge_N)")
            # Create simulated components for each Alice basis
            for alice_basis in ['X', 'Y']:
                obs_list.append(H1_N(conf, alice_basis=alice_basis, calc=calc))
                obs_list.append(V_N(conf, alice_basis=alice_basis, calc=calc))

                derived_obs.append(BobsEnergy_N(conf, alice_basis=alice_basis, calc=calc))

            obs_list.append(Charge_N(conf, apply_protocol=True, calc=calc))

        elif conf.N == 2:
            obs_list = [H1_B(conf, calc), V_AB(conf, calc), Charge(conf, True, calc)]
            derived_obs.append(BobsEnergy_N2(conf, calc))
        else:
            raise ValueError(f"Unsupported N={conf.N}")

        self.derived_observables.extend(derived_obs)

        return obs_list
