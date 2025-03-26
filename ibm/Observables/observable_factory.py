from .h1 import H1
from .v import V
from .charge import Charge
from .current import Current
from .total_energy import TotalEnergy # Import the new class
from .observable import Observable
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
        self.obs_list = [
            H1(conf),
            V(conf),
            Charge(conf, True, conf.theta),
            Charge(conf, False),
            Current(conf, True),
            Current(conf, False)
        ]
        # Create instances of derived observables (don't add to obs_list used for running sims)
        derived_obs = [
            TotalEnergy(conf.h, conf.k)
        ]

        # Create a dictionary for easy lookup by name
        self.obs_dict = {obs.name: obs for obs in self.obs_list + derived_obs}

        # Return only the list of observables to be simulated
        return self.obs_list

    def get_observable(self, name: str) -> Observable | None:
        return self.obs_dict.get(name)
