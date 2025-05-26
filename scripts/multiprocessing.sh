#!/bin/bash

# Parse command line arguments
script=$1
shift
while getopts ":i:o:B:h:s:-:" opt; do
    case $opt in
    i)
        input_file="$OPTARG"
        ;;
    o)
        output_file="$OPTARG"
        ;;
    B)
        buckets="$OPTARG"
        ;;
    h)
        hash="$OPTARG"
        ;;
    s)
        search="$OPTARG"
        ;;
    -)
        case "${OPTARG}" in
        hash)
            hash="${!OPTIND}"
            OPTIND=$((OPTIND + 1))
            ;;
        search)
            search="${!OPTIND}"
            OPTIND=$((OPTIND + 1))
            ;;
        *)
            echo "Invalid option --${OPTARG}" >&2
            exit 1
            ;;
        esac
        ;;
    \?)
        echo "Invalid option -$OPTARG" >&2
        exit 1
        ;;
    esac
done

# Validate required arguments
if [ -z "$input_file" ] || [ -z "$output_file" ] || [ -z "$buckets" ] || [ -z "$script" ]; then
    echo "Usage: $0 -i <input_file> -o <output_file> -B <buckets> -s <script> [-h hash] [-S search]"
    exit 1
fi

# Run video processing in parallel
start_time=$(date +%s.%N)
for ((i = 0; i < buckets; i++)); do
    cmd="PYTHONPATH=. python -Ou \"$script\" -i \"$input_file\" -o \"$output_file\" -B \"$buckets\" -b \"$i\""
    if [ -n "$hash" ]; then
        cmd="$cmd --hash \"$hash\""
    fi
    if [ -n "$search" ]; then
        cmd="$cmd --search \"$search\""
    fi
    eval "$cmd" &
done

wait

end_time=$(date +%s.%N)
execution_time=$(echo "$end_time - $start_time" | bc)
echo "Execution time: $execution_time seconds"
