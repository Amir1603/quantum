#!/bin/bash

errors=("bit-flip-errors" "alice-phase-flip-errors" "bob-phase-flip-errors" "excited-mixture-errors" "excited-superposition-errors")
Ns=(1 2 3)

for N in "${Ns[@]}"
do
    echo "Running: N$N"
    echo | python main.py --both-alice-values -Js 100 -N $N -o "N$N" -s Alice --alice-base X

    if [[ $N -gt 1 ]]; then
        echo | python main.py --both-alice-values -Js 100 -N $N -o "N$N""_X" -s NearestNeighbors --alice-base X
        echo | python main.py --both-alice-values -Js 100 -N $N -o "N$N""_Y" -s NearestNeighbors --alice-base Y
    fi

    for err in "${errors[@]}"
    do
        dir="N$N-$err"
        echo "Running: $dir"
        echo | python main.py -Js 8 -N $N --$err -o $dir -s Alice --alice-base X
        if [[ $N -gt 1 ]]; then
            echo | python main.py -Js 8 -N $N --$err -o $dir"_X" -s NearestNeighbors --alice-base X
            echo | python main.py -Js 8 -N $N --$err -o $dir"_Y" -s NearestNeighbors --alice-base Y
        fi
    done
done
