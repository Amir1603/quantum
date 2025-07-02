TODO:
* For Yaron:
1) Plot together both Alice's bases in NN simulation.
2) Fix errors injection.
3) Run on real HW for more stats.
* Extra:
1) Fix `run_all` script.
2) Fix analytical_tfim and tests.


| Hamiltonian | N | Alice Basis | E Status (10k) | Q Status (10k) | E Status (500k) | Q Status (500k) |
|-------------|---|-------------|----------------|----------------|-----------------|-----------------|
| Alice       | 1 | X           | V              | V              | V               | V               |
| Alice       | 2 | X           | V              | V              | V               | V               |
| Alice       | 3 | X           | V              | V              | V               | V               |
| NN          | 2 | X           | X              | V              | ~V              | V               |
| NN          | 3 | X           | X              | V              | X               | V               |
| NN          | 2 | Y           | VX             | ~V             | V               | V               |
| NN          | 3 | Y           | X              | X              |                 |                 |
