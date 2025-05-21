#!/bin/bash

errors=("classical-errors" "bit-flip-errors" "alice-phase-flip-errors" "bob-phase-flip-errors" "excited-mixture-errors" "excited-superposition-errors")
Ns=(2 3 4)

for N in "${Ns[@]}"
do
    # Prefer analytical calculations if possible
    if [ "$N" -eq 2 ]; then
        dir="N$N-Analytical"
        echo "Running: $dir"
        echo | python main.py --run-analytical --both-alice-values -Js 40 -N $N -o $dir
    else
        dir="N$N-Numerical"
        echo "Running: $dir"
        echo | python main.py --both-alice-values -Js 40 -N $N -o $dir
    fi

    for err in "${errors[@]}"
    do
        # Prefer analytical calculations if possible
        if [ "$N" -eq 2 ]; then
            dir="N$N-Analytical-$err"
            echo "Running: $dir"
            echo | python main.py --run-analytical -Js 7 -N $N --$err -o $dir
        else
            dir="N$N-Numerical-$err"
            echo "Running: $dir"
            echo | python main.py -Js 7 -N $N --$err -o $dir
        fi
    done
done
