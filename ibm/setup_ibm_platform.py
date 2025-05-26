from qiskit_ibm_runtime import QiskitRuntimeService

# Save an IBM Quantum account and set it as your default account.
QiskitRuntimeService.save_account(
    channel="ibm_cloud",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/92adc7cbe49a453d8112c867c9ee21a6:7ea25023-8d5c-42b3-b6db-0be958ef929b::",
    token="pQEdEQlNKTo9cn_6SWTEWQhqiuau3xYVk-j8F_X05eAb",
    set_as_default=True,
    # Use `overwrite=True` if you're updating your token.
    overwrite=True,
)

# Load saved credentials
service = QiskitRuntimeService()
