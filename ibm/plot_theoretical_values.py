import numpy as np
from Calculators import NumericalTFIM
import utils
from conf import Conf, ErrorsConf
from numerical_run_conf import SingleNumericalRunConf, NumericalRunConf
from plot_utils import PlotProperties

def binary_entropy(x):
    """ Calculates the binary entropy h(x). """
    x = np.clip(x, 1e-9, 1 - 1e-9) # Avoid log(0)
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)
def single_run(conf: Conf, alice_base: utils.AliceBase, hamiltonian_class: type, OB_types: dict[str, type]):
    OBs = {k: OB_class(conf.h, conf.J, conf.N, alice_base) for k, OB_class in OB_types.items()}
    H = hamiltonian_class(conf.h, conf.J, conf.N)

    ntfim = NumericalTFIM(H, list(OBs.values()))
    ntfim.calc_probabilities(conf)

    for v in OBs.values():
        if not hasattr(v, 'probabilities'):
            # Fallback if calc_probabilities is not yet implemented in NumericalTFIM
            # This allows the user's old code to run without crashing
            print("Warning: 'NumericalTFIM.calc_probabilities(conf)' is not yet implemented.")
            print("         Please implement it to return v.probabilities dict.")
            print("         Falling back to old 'calc_all(conf)' for now. Security analysis will fail.")
            ntfim.calc_all(conf) # Run the old function as a fallback
            break # Exit loop, v.teleported_values is populated by calc_all

        # Calculate expectation values from probabilities
        if False not in v.probabilities or True not in v.probabilities:
             # Handle cases where probabilities might not be calculated
             print(f"Warning: Probabilities not found for {v}. Setting teleported_values to 0.")
             v.teleported_values = {False: 0.0, True: 0.0}
             continue

        # For a=0 (False)
        p_false = v.probabilities[False]

        if not v.teleported_values:
            v.teleported_values = {}

        v.teleported_values[False] = p_false['p_plus'] - p_false['p_minus']
        
        # For a=1 (True)
        p_true = v.probabilities[True]
        v.teleported_values[True] = p_true['p_plus'] - p_true['p_minus']

    return OBs

def run_Js(rc: SingleNumericalRunConf):
    confs = Conf.generate_J_for_h(Conf(rc.N), 100)
    Js = [c.J for c in confs]
    ys = {}

    print(f"Running all Js ({len(Js)})")

    for c in confs:
        OBs = single_run(c, rc.alice_basis, rc.H_type, rc.OB_types)

        for name, v in OBs.items():
            if name not in ys:
                ys[name] = {False: [], True: []}

            ys[name][False].append(v.teleported_values[False])
            ys[name][True].append(v.teleported_values[True])

    for name, y_vals in ys.items():
        rc.J_pps[name].update_x("J", np.array(Js))

        a0_vals = np.array(y_vals[False])
        a1_vals = np.array(y_vals[True])

        rc.J_pps[name].update_ys(name, f"a=0", np.array(a0_vals))
        rc.J_pps[name].update_ys(name, f"a=1", np.array(a1_vals))

def run_hs(rc: SingleNumericalRunConf):
    confs = Conf.generate_h_for_J(Conf(rc.N), 100)
    hs = [c.h for c in confs]
    ys = {}

    print(f"Running all hs ({len(hs)})")

    for c in confs:
        OBs = single_run(c, rc.alice_basis, rc.H_type, rc.OB_types)

        for name, v in OBs.items():
            if name not in ys:
                ys[name] = {False: [], True: []}

            ys[name][False].append(v.teleported_values[False])
            ys[name][True].append(v.teleported_values[True])

    for name, y_vals in ys.items():
        rc.h_pps[name].update_x("h", np.array(hs))

        a0_vals = np.array(y_vals[False])
        a1_vals = np.array(y_vals[True])

        rc.h_pps[name].update_ys(name, f"a=0", a0_vals)
        rc.h_pps[name].update_ys(name, f"a=1", a1_vals)

def run_single_error(errs: list[ErrorsConf], conf: Conf, rc: SingleNumericalRunConf, err_name: str, run_J: bool = True):
    confs = [c for c in Conf.generate_from_errors(conf, errs)]
    p_errs = [err_conf.__dict__[err_name] for err_conf in errs]
    ys = {}

    if run_J:
        print(f"Running {err_name} for J={conf.J}")
    else:
        print(f"Running {err_name} for N={conf.N}")

    for c in confs:
        OBs = single_run(c, rc.alice_basis, rc.H_type, rc.OB_types)

        for name, v in OBs.items():
            if name not in ys:
                ys[name] = []

            ys[name].append(v.teleported_values[False])

    for name, y_vals in ys.items():
        if run_J:
            rc.errs_pps[name][err_name].update_x(err_name, np.array(p_errs))
            rc.errs_pps[name][err_name].update_ys(name, f"J={conf.J}", np.array(y_vals), y_lim=NumericalRunConf.get_ylim(err_name, name, rc.H_type))
        else:
            rc.class_comm_errs_N_pps[name].update_x(err_name, np.array(p_errs))
            rc.class_comm_errs_N_pps[name].update_ys(name, f"N={conf.N}", np.array(y_vals), y_lim=NumericalRunConf.get_ylim(err_name, name, rc.H_type))

def run_errors(rc: SingleNumericalRunConf):
    Js = np.linspace(1.0, 4.0, 7).tolist()
    print("Running all errors")

    for err_name in NumericalRunConf.get_errors():
        conf = Conf(rc.N)
        errs = NumericalRunConf.generate_errors_configurations(err_name)

        for J in Js:
            conf.J = J
            run_single_error(errs, conf, rc, err_name)

def run_security_analysis(run_conf: NumericalRunConf, N: int, J: float, h: float):
    """
    Runs the full security analysis for a given N, J, and h by calculating
    e_bit (from X0 basis) and e_phase (from Y0 basis) as a function of
    phase-flip noise on Bob's site.
    """
    print(f"Running Security Analysis for {run_conf.name} N={N}, J={J}, h={h}...")
    try:
        # Find the specific config objects for the Key (X0) and Test (Y0) bases
        rc_key_basis = next(r for r in run_conf.confs if r.alice_basis == utils.AliceBase.X and r.N == N)
        rc_test_basis = next(r for r in run_conf.confs if r.alice_basis == utils.AliceBase.Y and r.N == N)
    except StopIteration:
        print(f"Error: Could not find X0 and Y0 configs for N={N}.")
        print("Skipping security analysis for this N.")
        return None

    err_name = 'p_bob_phaseflip_error' # This is the noise we are plotting against
    
    # Generate a range of error probabilities (51 points from 0.0 to 0.5)
    base_conf = Conf(N) # Create a base config
    base_conf.J = J
    base_conf.h = h
    err_confs_list = NumericalRunConf.generate_errors_configurations(err_name, num_points=51, p_max=0.5)
    ps = [ec.__dict__[err_name] for ec in err_confs_list]
    
    # Create the list of config objects, each with a different error probability
    confs_with_errors = [c for c in Conf.generate_from_errors(base_conf, err_confs_list)]

    e_bits, e_phases, k_asyms, sift_rates, k_totals = [], [], [], [], []
    
    print(f"Looping over {len(confs_with_errors)} noise points for security analysis...")

    for conf_with_err in confs_with_errors:
        
        # --- 1. Key Basis Run (sigma_A = X0) -> to get e_bit ---
        OBs_key = single_run(conf_with_err, rc_key_basis.alice_basis, rc_key_basis.H_type, rc_key_basis.OB_types)
        charge_OB_key = OBs_key.get('charge') # Get the Charge observable
        
        if charge_OB_key is None or not hasattr(charge_OB_key, 'probabilities'):
            print(f"Error: 'Charge' observable or its probabilities not found. Aborting security analysis. {charge_OB_key}")
            return None

        probs_key = charge_OB_key.probabilities[False] # Use a=0 (logical '1')
        p_plus_key = probs_key['p_plus']   # Prob of getting +1 (Error)
        p_minus_key = probs_key['p_minus'] # Prob of getting -1 (Correct)

        # Calculate QBER (e_bit)
        denominator_key = p_plus_key + p_minus_key + 1e-9 # Add epsilon to avoid div by zero
        e_bit = p_plus_key / denominator_key
        
        # Calculate Sifting Rate (for 0/1 outcomes, assuming 50% basis choice)
        sift_rate = 0.5 * (p_plus_key + p_minus_key)

        # --- 2. Test Basis Run (sigma_A = Y0) -> to get e_phase ---
        OBs_test = single_run(conf_with_err, rc_test_basis.alice_basis, rc_test_basis.H_type, rc_test_basis.OB_types)
        charge_OB_test = OBs_test.get('charge')

        if charge_OB_test is None or not hasattr(charge_OB_test, 'probabilities'):
             print("Error: 'Charge' (Test) observable or its probabilities not found. Aborting.")
             return None

        probs_test = charge_OB_test.probabilities[False] # Use a=0
        p_plus_test = probs_test['p_plus']   # Prob of getting +1 (Error in test basis)
        p_minus_test = probs_test['p_minus'] # Prob of getting -1 (Correct in test basis)

        # Calculate Test Error Rate (e_phase)
        denominator_test = p_plus_test + p_minus_test + 1e-9
        e_phase = p_plus_test / denominator_test
        
        # --- 3. Calculate Key Rates ---
        k_asym_val = 1.0 - binary_entropy(e_bit) - binary_entropy(e_phase)
        k_asym = max(0.0, k_asym_val) # Key rate can't be negative
        
        k_total = sift_rate * k_asym

        # --- 4. Store results ---
        e_bits.append(e_bit)
        e_phases.append(e_phase)
        k_asyms.append(k_asym)
        sift_rates.append(sift_rate)
        k_totals.append(k_total)

    # --- 5. Plotting ---
    plot_path = f"{run_conf.name}/security_analysis/N{N}/key_rates_vs_{err_name}_J{J:.2f}_h{h:.2f}.png"
    pp = PlotProperties(plot_path)
    pp.update_x(f"Noise Probability (p_bob_phaseflip_error)", np.array(ps))
    pp.update_ys("Rate", "e_bit (QBER)", np.array(e_bits), y_lim=(0, 0.5))
    pp.update_ys("Rate", "e_phase (Test Basis Error)", np.array(e_phases), y_lim=(0, 0.5))
    pp.update_ys("Rate", "K_asym (Asymptotic Rate)", np.array(k_asyms), y_lim=(0, 1.0))
    pp.update_ys("Rate", "K_total (Sifted Rate)", np.array(k_totals), y_lim=(0, 0.5))
    
    print(f"Security analysis complete. Plot saved to {plot_path}")
    return pp

if __name__ == "__main__":
    run_confs = [NumericalRunConf.AliceConf(), NumericalRunConf.NNConf()]
    pps = []

    for run_conf in run_confs:
        combined_alice_base_J_pps = {}
        combined_alice_base_h_pps = {}

        for rc in run_conf.confs:
            print(f"Calculating theoretical values for {rc.name} with AliceBase={rc.alice_basis} and N={rc.N}...")

            run_Js(rc)
            run_hs(rc)
            run_errors(rc)

            # Get list with all PlotProperties objects
            # No PlotProperties for class_comm_err vs N and for combined alice_base for NN
            pps.extend(rc.get_all_pps())

            for k, v in rc.J_pps.items():
                new_key = f"{rc.name}_{rc.N}_{k}"

                if new_key not in combined_alice_base_J_pps:
                    combined_alice_base_J_pps[new_key] = PlotProperties(f"{rc.name}/both_bases/N{rc.N}/{k}_vs_J.png")

                combined_alice_base_J_pps[new_key].update_x("J", v.x_vals)
                y_vals, y_lim = v.ys["a=0"]
                combined_alice_base_J_pps[new_key].update_ys(k, f"a=0, alice_basis={rc.alice_basis}", y_vals, y_lim)
                y_vals, y_lim = v.ys["a=1"]
                combined_alice_base_J_pps[new_key].update_ys(k, f"a=1, alice_basis={rc.alice_basis}", y_vals, y_lim)
            
            for k, v in rc.h_pps.items():
                new_key = f"{rc.name}_{rc.N}_{k}"

                if new_key not in combined_alice_base_h_pps:
                    combined_alice_base_h_pps[new_key] = PlotProperties(f"{rc.name}/both_bases/N{rc.N}/{k}_vs_h.png")

                combined_alice_base_h_pps[new_key].update_x("h", v.x_vals)
                y_vals, y_lim = v.ys["a=0"]
                combined_alice_base_h_pps[new_key].update_ys(k, f"a=0, alice_basis={rc.alice_basis}", y_vals, y_lim)
                y_vals, y_lim = v.ys["a=1"]
                combined_alice_base_h_pps[new_key].update_ys(k, f"a=1, alice_basis={rc.alice_basis}", y_vals, y_lim)

        if run_conf.name == "nn": # Only run for H(2) which has X0 and Y0 bases
            # Get all N values present in this run_conf
            Ns_in_conf = sorted(list(set(rc.N for rc in run_conf.confs)))
            
            for N_sec in Ns_in_conf:
                # We need to pick specific J and h for this analysis.
                # Let's use J=2.0 (seems a reasonable signal strength) and h=1.0
                # You can change these values or add a loop.
                J_sec = 2.0
                h_sec = 1.0
            
                security_pp = run_security_analysis(run_conf, N=N_sec, J=J_sec, h=h_sec)
                if security_pp:
                    pps.append(security_pp)

        if len(combined_alice_base_J_pps) > 1:
            pps.extend(combined_alice_base_J_pps.values())
        if len(combined_alice_base_h_pps) > 1:
            pps.extend(combined_alice_base_h_pps.values())

        class_comm_run_confs = [SingleNumericalRunConf(run_conf.name, run_conf.H_type, run_conf.OB_types, basis) for basis in run_conf.alice_bases]

        for rc in class_comm_run_confs:
            print(f"Calculating classical communication error vs N for {rc.name} with AliceBase={rc.alice_basis}...")
            for N in NumericalRunConf.generate_class_comm_error_Ns(rc.name):
                conf = Conf(N)
                conf.J = 1.0
                errs = ErrorsConf.generate_classical_error()

                run_single_error(errs, conf, rc, 'p_classical_error', run_J=False)
                pps.extend(rc.class_comm_errs_N_pps.values())

    for pp in pps:
        pp.plot()
