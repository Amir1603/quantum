#!/bin/bash

errors=("classical-errors" "bit-flip-errors" "alice-phase-flip-errors" "bob-phase-flip-errors" "excited-mixture-errors" "excited-superposition-errors")
Ns=(1 2 3)

for N in "${Ns[@]}"
do
    dir="N$N"
    echo "Running: $dir"
    echo | python main.py --both-alice-values -Js 100 -N $N -o $dir

    for err in "${errors[@]}"
    do
        dir="N$N-$err"
        echo "Running: $dir"
        echo | python main.py -Js 8 --avoid-J0 -N $N --$err -o $dir
    done
done
