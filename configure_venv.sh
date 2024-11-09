#!/bin/bash

python -m venv ibm/.venv/cwq
source ibm/.venv/cwq/bin/activate

pip install -r ibm/requirements.txt