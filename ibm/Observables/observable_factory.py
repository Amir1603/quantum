from .h1 import H1
from .v import V
from .charge import Charge
from .current import Current
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
        self.obs_list = []

    def create_observables(self, conf: Conf) -> list[Observable]:
        self.obs_list = [H1(conf), V(conf), Charge(conf, True), Charge(conf, False), Current(conf, True), Current(conf, False)]
        return self.obs_list