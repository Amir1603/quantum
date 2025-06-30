TODO:
1) Alice base & NN Hamiltonian:
    * Fix and make sure simulation works for NN Hamiltonian
        - Fix `apply_measurements` in runner for Bob's neighbor?
        - Should the roation angles be fixed?
        - Something else?
    * Run simulation for NN on both Alice's bases and plot together
2) Finalize also theoretical expressions for the teleported\extracted values to plot them as well in the numerical calculations.
3) Fix classical communication error.
4) Run on real HW for more stats.
5) Complete numerical theoretic modeling for `AliceBasis='Y'`.
6) Fix `run_all` script.
7) Fix analytical calculations and tests.


------------------------------------------------------------------
|    Hamiltonian    |    N    |    Alice Basis    |    Status    |
|       Alice       |    2    |         X         |      V       |
|       Alice       |    3    |         X         |      V       |
|        NN         |    2    |         X         |    X (E)     |
|        NN         |    3    |         X         |    X (E)     |
|        NN         |    2    |         Y         |      X       |
|        NN         |    3    |         Y         |      X       |
------------------------------------------------------------------