#!/bin/bash

# Directory containing the CSV files
dir="core_dataset"

# Create a temporary file to store concatenated results
temp_file="$dir/temp_concatenated.csv"
>"$temp_file" # Clear/create empty temp file
log_files=("$dir"/video_process_*.log)
metadata_files=("$dir"/metadata_*.csv)
hashes_dir=("$dir"/hashes/*)

first_file=true
metadata_files=("$dir"/metadata_*.csv)
for file in "${metadata_files[@]}"; do
    # Check if file exists and is not empty
    # Keep header for first file and remove it for next files

    if [ -s "$file" ]; then
        if $first_file; then
            cat "$file" >>"$temp_file"
            first_file=false
        else
            tail -n +2 "$file" >>"$temp_file"
        fi
    fi
done

# Concatenate all log files and sort them
if [ ${#log_files[@]} -gt 0 ]; then
    cat "${log_files[@]}" >"$dir/video_process.log"
else
    echo "No log files found to concatenate"
fi
sort -k2,3 -o "$dir/video_process.log" "$dir/video_process.log"

# Process time_* files in each subfolder of hashes
for dir_hash in "${hashes_dir[@]}"; do
    if [ -d "$dir_hash" ]; then
        temp_time_file="$dir_hash/temp_time.csv"
        >"$temp_time_file"

        # Process each time_* file in this directory
        first_time_file=true
        for time_file in "$dir_hash/time_"*.csv; do
            if [ -s "$time_file" ]; then
                if $first_time_file; then
                    cat "$time_file" >>"$temp_time_file"
                    first_time_file=false
                else
                    tail -n +2 "$time_file" >>"$temp_time_file"
                fi
            fi
        done

        # If temp file is not empty, move it to final destination
        if [ -s "$temp_time_file" ]; then
            mv "$temp_time_file" "$dir_hash/time.csv"
            echo "Time files in $dir_hash/ successfully concatenated to $dir_hash/time.csv"
        else
            rm "$temp_time_file"
            echo "No valid time files found in $dir_hash/time.csv"
        fi
    fi
done

# If temp file is not empty, move it to final destination
if [ -s "$temp_file" ]; then
    mv "$temp_file" "$dir/metadata.csv"
    
    echo "Log files $dir/video_process_*.log successfully concatenated and sorted to $dir/video_process.txt"
    echo "Files $dir/metadata_*.csv successfully concatenated to $dir/metadata.csv"

    if [ -n "$metadata_files" ]; then
        rm -f "${metadata_files[@]}"
    fi
    if [ -n "$log_files" ]; then
        rm -f "${log_files[@]}"
    fi
    if [ -n "$hashes_dir" ]; then
        for dir in "${hashes_dir[@]}"; do
            rm -f "$dir"/time_*.csv
        done
    fi
else
    rm "$temp_file"
    echo "No valid files found to concatenate"
fi
