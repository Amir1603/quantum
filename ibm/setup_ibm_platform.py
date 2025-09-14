from qiskit_ibm_runtime import QiskitRuntimeService

# Save an IBM Quantum account and set it as your default account.
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",

    # amiryona@mail.tau.ac.il
    # instance = "crn:v1:bluemix:public:quantum-computing:us-east:a/520e7150f9cf4984aba778477ab14bb9:bb690880-6936-43b0-93b1-d780be5a7b84::",
    # token = "xI71GPjFW6oVfClPxXX8QaxiwIXnCex1H-hmm2fjhRRo",
    # name = "amiryona-tau",

    # yonaamir@gmail.com
    # instance = "crn:v1:bluemix:public:quantum-computing:us-east:a/92adc7cbe49a453d8112c867c9ee21a6:7ea25023-8d5c-42b3-b6db-0be958ef929b::",
    # token = "pQEdEQlNKTo9cn_6SWTEWQhqiuau3xYVk-j8F_X05eAb",
    # name = "yonaamir",

    # noyavraham3@gmail.com
    # Open
    instance = "crn:v1:bluemix:public:quantum-computing:us-east:a/a3bb5d1d765e4c49b1c3bc0d8076444e:0919c3a5-19f7-4f3d-98de-c1e299fd4c54::",
    # Payed
    # instance = "crn:v1:bluemix:public:quantum-computing:us-east:a/a3bb5d1d765e4c49b1c3bc0d8076444e:cf387a6b-3c01-4d6b-a909-da1eaa63ae7c::",
    token = "xX9lecB631A73LN23FnK-iGQ8UnxVQnz-1v01uH4gFoi",
    name = "Noy Avraham",

    set_as_default=True,
    # Use `overwrite=True` if you're updating your token.
    overwrite=True,
)

# Load saved credentials
service = QiskitRuntimeService()
