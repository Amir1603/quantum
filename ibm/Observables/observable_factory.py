from .h1 import H1_B
from .v import V_AB
from .charge import Charge
from .current import Current
from .total_energy import TotalEnergy # Import the new class
from .observable import Observable
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
        # Create instances of directly simulated observables
        if conf.N == 3:
            self.obs_list = [
                Energy_N3(conf, alice_basis='X'),
                Energy_N3(conf, alice_basis='Y'),
                Charge(conf, True),
            ]
            derived_obs = []
        elif conf.N == 2:
            self.obs_list = [H1_B(conf), V_AB(conf), Charge(conf, True)]
            derived_obs = [TotalEnergy(conf)]
        else:
            raise ValueError(f"Unsupported N={conf.N}")

        # Create a dictionary for easy lookup by name
        self.obs_dict = {obs.name: obs for obs in self.obs_list + derived_obs}

        return self.obs_list

    def get_observable(self, name: str) -> Observable | None:
        return self.obs_dict.get(name)
