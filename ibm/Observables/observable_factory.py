from .h1 import H1_B
from .v import V_AB
from .charge import Charge
from .charge_n3 import Charge_N3
from .current import Current
from .bobs_energy_n2 import BobsEnergy_N2
from .observable import Observable
from .h1_n3 import H1_N3
from .v_n3 import V_N3
from .energy_n3 import Energy_N3
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

    def create_observables(self, conf: Conf) -> list[Observable]:
        derived_obs = []
        obs_list: list[Observable] = []

        # Create instances of directly simulated observables
        if conf.N == 3:
            print("Creating N=3 observables (H1, V components + derived E_B + Charge_N3)")
            # Create simulated components for each Alice basis
            for alice_basis in ['X', 'Y']:
                obs_list.append(H1_N3(conf, alice_basis=alice_basis))
                obs_list.append(V_N3(conf, alice_basis=alice_basis))

                derived_obs.append(Energy_N3(conf, alice_basis=alice_basis))

            obs_list.append(Charge_N3(conf, apply_protocol=True))

        elif conf.N == 2:
            obs_list = [H1_B(conf), V_AB(conf), Charge(conf, True)]
            derived_obs.append(BobsEnergy_N2(conf))
        else:
            raise ValueError(f"Unsupported N={conf.N}")

        self.derived_observables.extend(derived_obs)

        return obs_list
