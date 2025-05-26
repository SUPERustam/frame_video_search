#!/bin/bash

# Parse command line arguments
while getopts "i:" opt; do
    case $opt in
    i) dir="$OPTARG" ;;
    \?)
        echo "Usage: $0 -i input_directory" >&2
        exit 1
        ;;
    esac
done

# Check if input directory is provided
if [ -z "$dir" ]; then
    echo "Error: No input directory provided. Usage: $0 -i input_directory" >&2
    exit 1
fi

# Find all directories except 'hashes', 'query_hashes' and 'quality_plots'
hashes_dir=$(find "$dir" -type d ! -name "hashes" ! -name "query_hashes" ! -name "quality_plots" ! -path "$dir")

time_folders=()
# Find all directories containing time_*.csv files
for dir_hash in $hashes_dir; do
    if find "$dir_hash" -maxdepth 1 -name "time_*.csv" | read -r; then
        time_folders+=("$dir_hash")
    fi
done

# Concatenate all log files and sort them
log_files=("$dir"/search_process_*.log)

if [ ${#log_files[@]} -gt 0 ]; then
    cat "${log_files[@]}" >"$dir/search_process.log"
else
    echo "No log files found to concatenate"
fi
sort -k1,2 -o "$dir/search_process.log" "$dir/search_process.log"

# Process time_* files in each subfolder of hashes
for dir_hash in "${time_folders[@]}"; do
    if [ -d "$dir_hash" ]; then
        temp_time_file="$dir_hash/temp_time.csv"
        >"$temp_time_file"

        # Process each time_* file in this directory
        first_time_file=true
        for time_file in "$dir_hash"/time_*.csv; do
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
            echo "Time files in $dir_hash successfully concatenated to $dir_hash/time.csv"
        else
            echo "rm temp_time_file"
            rm "$temp_time_file"
            echo "No valid time files found in $dir_hash/time.csv"
        fi
    fi
done


echo "Log files $dir/search_process_*.log successfully concatenated and sorted to $dir/search_process.log"
echo "Remove log_files"
if [ -n "$log_files" ]; then
    rm -f "${log_files[@]}"
fi

echo "Remove time_folders"
if [ -n "$time_folders" ]; then
    for dir in "${time_folders[@]}"; do
        rm -f "$dir"/time_*.csv
    done
fi
