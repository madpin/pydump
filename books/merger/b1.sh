#!/bin/bash

# --- Configuration ---
input_dir="/Users/tpinto/Downloads/Long Walk to Freedom"
output_file="/Users/tpinto/Downloads/Long Walk to Freedom.mp3"
temp_prefix="intermediate_"

# --- Helper Functions ---
log_error() {
    echo "Error: $*" >&2
    return 1
}

log_info() {
    echo "Info: $*"
}

cleanup_temp_files() {
    if [ -n "$temp_files" ]; then
        IFS='|' read -ra temp_files_array <<< "$temp_files"
        for temp_file in "${temp_files_array[@]}"; do
            log_info "Removing temp file: $temp_file"
            if [ -e "$temp_file" ]; then
                rm "$temp_file"
            else
                log_error "Temp file not found '$temp_file'. Could not be deleted"
            fi
        done
    # reset temp files
    temp_files=""
    fi
}

# --- Main Script ---
log_info "Starting processing..."

# Remove pre-existing temp files
find /tmp -type f -name "${temp_prefix}*.ts" -delete

# Initialize variable to store name of temporary files
temp_files=""

# Check if input directory exists
if [ ! -d "$input_dir" ]; then
    log_error "Input directory '$input_dir' does not exist."
    exit 1
fi

# Find all mp3 files recursively, sort them, and convert them to .ts files
find "$input_dir" -type f -name "*.mp3" -print0 | sort -z | while IFS= read -r -d $'\0' file; do
    # Create a unique temporary file name
    temp_file=$(mktemp -t "${temp_prefix}XXXXXXXXXX.ts")
    if [ -z "$temp_file" ]; then
        log_error "mktemp failed to create temporary file."
        cleanup_temp_files
        exit 1
    fi
    log_info "Creating temporary file: $temp_file"

    # Convert the current mp3 to a temporary file.
    # Here we use the -y flag to force overwrite.
    ffmpeg -y -i "$file" -c copy -f mpegts "$temp_file"
    if [ $? -ne 0 ]; then
        log_error "ffmpeg failed to convert '$file' to '$temp_file'."
        cleanup_temp_files
        exit 1
    fi

    # Append the temporary file to the list
    temp_files="$temp_files|$temp_file"
done

# Concatenate all the temporary files
if [ -n "$temp_files" ]; then
  # Remove leading pipe char
  temp_files=${temp_files:1}
  temp_files_for_concat=$(printf "%s\n" "file '$temp_files'" | sed 's/|/\\nfile /g')

    # Use ffmpeg to concatenate the files
    log_info "Concatenating files into: $output_file"
    ffmpeg -f concat -safe 0 -i <(echo "$temp_files_for_concat") -c copy "$output_file"
    if [ $? -ne 0 ]; then
        log_error "ffmpeg failed to concatenate files."
        cleanup_temp_files
        exit 1
    fi

    # Remove all intermediate files
    cleanup_temp_files

else
    log_info "No mp3 files found in '$input_dir' or its subdirectories. Nothing to concatenate."
fi

log_info "Processing finished."
exit 0
