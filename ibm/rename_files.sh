#!/bin/bash

cd artifacts

# Create destination folder
output_folder="All"
mkdir -p "$output_folder"

# Loop through all directories like a1-b1-c1
for dir in */; do
    dir_name="${dir%/}"

    prefix="${dir_name%-*}"
    prefix="${prefix//-/_}"

    obs=("charge.png" "E_B.png")

    for O in "${obs[@]}"
    do
        # Match files using a known suffix pattern
        for file in "$dir"*$O; do
            # Get base filename only
            base=$(basename "$file")

            new_name="${prefix}_${O}"
            cp "$file" "$output_folder/$new_name"
        done
    done
done

cd ..
