from qiskit_ibm_runtime import QiskitRuntimeService

# Save an IBM Quantum account and set it as your default account.
QiskitRuntimeService.save_account(
    channel="ibm_quantum",
    token="e9344a377d64f71cd337bf0ccfa9553f76ddcbf0573b42fcf5bf3ffb2f57dc7f5f48f055fd9fa918871dfa09dd9577a7009a36f33f965076d0130dfa985bd755",
    set_as_default=True,
    # Use `overwrite=True` if you're updating your token.
    overwrite=True,
)

# Load saved credentials
service = QiskitRuntimeService()
