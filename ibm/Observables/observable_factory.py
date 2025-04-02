from .h1 import H1_B
from .v import V_AB
from .charge import Charge
from .current import Current
from .total_energy import TotalEnergy # Import the new class
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
        self.obs_list: list[Observable] = []
        self.obs_dict: dict[str, Observable] = {}

    def create_observables(self, conf: Conf) -> list[Observable]:
        derived_obs = []

        # Create instances of directly simulated observables
        if conf.N == 3:
            print("Creating N=3 observables (H1, V components + derived E_B)")
            # Create simulated components for each Alice basis
            for alice_basis in ['X', 'Y']:
                 self.obs_list.append(H1_N3(conf, alice_basis=alice_basis))
                 self.obs_list.append(V_N3(conf, alice_basis=alice_basis))

                 # Create derived E_B observable instances for each condition
                 # These depend on the final result (xor_alice_res) which might vary per run
                 # It's cleaner to create these during results processing, or create all possibilities here
                 for xor_res in [0, 1]:
                      derived_obs.append(Energy_N3(conf, alice_basis=alice_basis, xor_alice_res=xor_res))

        elif conf.N == 2:
            self.obs_list = [H1_B(conf), V_AB(conf), Charge(conf, True)]
            derived_obs.append(TotalEnergy(conf))
        else:
            raise ValueError(f"Unsupported N={conf.N}")

        # Create a dictionary for easy lookup by name
        self.obs_dict = {obs.name: obs for obs in self.obs_list + derived_obs}

        return self.obs_list

    def get_observable(self, name: str) -> Observable | None:
        return self.obs_dict.get(name)
