"""
Description: This script explores a directory, extracts metadata from audio files using the TinyTag library, and logs the information.

Features:
- Reads audio files from a specified directory (defaults to "./books-metadata/book-files/").
- Extracts metadata such as title, artist, album, duration, etc., using TinyTag.
- Logs the extracted metadata to the console in a user-friendly format.
- Saves the extracted metadata to a log file named "audio_metadata.log" inside a "logs" directory.
- Handles potential errors gracefully, such as files not being found or having unsupported formats.
- Allows configuration of the target directory via the BOOK_FILES_DIR environment variable.
- Informs the user if no audio files are found in the specified directory.

Required Environment Variables:
- BOOK_FILES_DIR (Optional): Specifies the directory containing audio files.

Required Packages:
- tinytag (install via pip: `pip install tinytag`)

Usage:
1. Set the BOOK_FILES_DIR environment variable to the desired directory (optional).
2. Run the script: `python your_script_name.py`

Author: tpinto
"""

import os
import logging
from tinytag import TinyTag, TinyTagException

# Define constants for better readability
DEFAULT_BOOK_FILES_DIR = "./books/book_files/"
LOG_FILE_NAME = "./logs/audio_metadata.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
    ".wav",
    ".wma",
    ".aiff",
    ".ape",
    ".dsf",
    ".opus",
}  # Add more if needed


def configure_logging():
    """Configures the logging settings."""
    logs_dir = os.path.dirname(LOG_FILE_NAME)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)  # Create logs directory if it doesn't exist

    logging.basicConfig(filename=LOG_FILE_NAME, level=logging.INFO, format=LOG_FORMAT)


def get_audio_metadata(file_path):
    """
    Extracts metadata from an audio file using TinyTag.

    Args:
        file_path: The path to the audio file.

    Returns:
        A dictionary containing the extracted metadata, or None if an error occurs.
    """
    try:
        tag = TinyTag.get(file_path, image=True)
        metadata = {
            "file": os.path.basename(file_path),
            "title": tag.title,
            "artist": tag.artist,
            "album": tag.album,
            "year": tag.year,
            "duration": tag.duration,
            "filesize": tag.filesize,
            "bitrate": tag.bitrate,
            "genre": tag.genre,
            "track": tag.track,
            "disc": tag.disc,
            "samplerate": tag.samplerate,
            "image_data": len(tag.get_image()) if tag.get_image() else 0,
        }
        return metadata
    except TinyTagException as e:
        logging.error(f"Error processing {file_path}: {e}")
        return None


def explore_directory(directory):
    """
    Explores a directory, processes audio files, and returns the number of files found.

    Args:
        directory: The directory to explore.

    Returns:
        The number of audio files found and processed.
    """
    audio_files_found = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in SUPPORTED_AUDIO_EXTENSIONS:
                file_path = os.path.join(root, file)
                metadata = get_audio_metadata(file_path)
                if metadata:
                    print_and_log_metadata(metadata)
                    audio_files_found += 1
    return audio_files_found


def print_and_log_metadata(metadata):
    """
    Prints metadata to the console and logs it to a file.

    Args:
        meta A dictionary containing the audio file metadata.
    """
    separator = "-" * 30
    print(separator)
    logging.info(separator)
    for key, value in metadata.items():
        message = f"{key}: {value}"
        print(message)
        logging.info(message)
    print(f"{separator}\n")
    logging.info(f"{separator}\n")


def main():
    """
    Main function to run the script.
    """
    configure_logging()  # Configure logging at the start

    target_directory = os.environ.get(
        "BOOK_FILES_DIR", DEFAULT_BOOK_FILES_DIR
    )  # Use constant

    if not os.path.exists(target_directory):
        print(f"Error: Directory '{target_directory}' not found.")
        logging.error(f"Directory '{target_directory}' not found.")
        return

    print(f"Exploring directory: {target_directory}")
    logging.info(f"Exploring directory: {target_directory}")

    audio_files_count = explore_directory(target_directory)

    if audio_files_count == 0:
        print(
            f"No audio files found in '{target_directory}'. "
            "Please check the directory or the supported file extensions."
        )
        logging.warning(f"No audio files found in '{target_directory}'.")
    else:
        print(f"Processed {audio_files_count} audio files.")


if __name__ == "__main__":
    main()
