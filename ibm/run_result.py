from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from Observables import Observable


@dataclass
class RunResult:
    """Holds all data for a single simulation/hardware execution."""
    # --- Experiment Identification ---
    observable: Observable
    conf_params: dict
    backend_name: str
    run_type: str # 'simulator', 'sampler'
    timestamp: datetime = field(default_factory=datetime.now)
    noise_params: dict = field(default_factory=dict) # e.g., {'p_dephase': 0.1} or {}

    # --- Raw Results ---
    counts: dict = field(default_factory=dict)
    total_shots: int = 0
    job_id: str | None = None # Optional (for HW runs)
    # circuit_depth: int | None = None # Optional metadata
    # transpiled_circuit_repr: str | None = None # Optional string representation

    # --- Calculated Values ---
    expectation_value: float | None = None
    sem: float | None = None # Standard Error of Mean
    susceptibility: float | None = None
    correlation: float | None = None # Example: Z0Z1 correlation

    # --- Derived Flag ---
    is_derived: bool = False # Flag for results like BobsEnergy

    def __post_init__(self):
        # Ensure correct types if loading from JSON etc.
        if self.counts is None: self.counts = {}
        if self.noise_params is None: self.noise_params = {}