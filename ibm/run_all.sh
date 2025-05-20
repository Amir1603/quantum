#!/bin/bash

errors=("classical-errors" "bit-flip-errors" "alice-phase-flip-errors" "bob-phase-flip-errors" "excited-mixture-errors" "excited-superposition-errors")
Ns=(2 3 4)

for N in "${Ns[@]}"
do
    for err in "${errors[@]}"
    do
        dir="N$N-Numerical-$err"
        echo "Running: $dir"
        python main.py --all-J-for-h --both-alice-values -N $N --$err -o $dir

        if [ "$N" -eq 2 ]; then
            dir="N$N-Analytical-$err"
            echo "Running: $dir"
            python main.py --all-J-for-h --both-alice-values --run-analytical -N $N --$err -o $dir
        fi
    done
done



