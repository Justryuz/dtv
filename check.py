import os
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # For progress tracking
import pyfiglet  # For ASCII art
import time

def print_ascii_art():
    """Print ASCII art with the codename 'justryuz'."""
    ascii_art = pyfiglet.figlet_format("justryuz", font="slant")  # Change "slant" to any available font
    print(ascii_art)
    time.sleep(20)

def check_url_with_requests(url, timeout, retries=3):
    """Check if a URL is live or dead using HTTP requests."""
    for attempt in range(retries):
        try:
            response = requests.head(url, timeout=timeout)
            if response.status_code == 200:
                return True  # URL is live
        except requests.RequestException as e:
            if attempt < retries - 1:
                continue  # Retry
            print(f"Error checking URL: {url} - {e}")
    return False  # URL is dead after retries

def process_stream(index, lines, timeout, verbose, retries):
    """Process a single stream URL and its metadata."""
    url = lines[index].strip()
    if check_url_with_requests(url, timeout, retries):
        if verbose:
            print(f"Live/Valid: {url}")
        return [lines[index - 1], lines[index]]  # Return the #EXTINF and URL lines
    else:
        if verbose:
            print(f"Dead/Invalid: {url}")
        return []

def check_streams(file_path, output_file, max_workers, timeout, verbose, retries):
    """Check streams in a single file and write live/valid streams to a new file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    live_lines = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_stream, i, lines, timeout, verbose, retries): i
            for i, line in enumerate(lines)
            if line.startswith("http")  # Check only URLs
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing URLs"):
            live_lines.extend(future.result())

    # Write the live/valid streams to a new M3U file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(live_lines)

    print(f"New M3U file with live/valid streams saved to: {output_file}")

def process_folder(input_folder, output_folder, max_workers, timeout, verbose, retries, extensions):
    """Process all specified media files in a folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(tuple(extensions)):
            input_file = os.path.join(input_folder, filename)
            output_file = os.path.join(output_folder, f"live_{filename}")
            print(f"Processing file: {input_file}")
            check_streams(input_file, output_file, max_workers, timeout, verbose, retries)

def combine_m3u8_files(output_folder, combined_file):
    """Combine all .m3u8 files in the output folder into a single playlist."""
    combined_lines = []
    for filename in os.listdir(output_folder):
        if filename.endswith(".m3u8"):
            file_path = os.path.join(output_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                combined_lines.extend(file.readlines())

    with open(combined_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(combined_lines)

    print(f"Combined playlist saved to: {combined_file}")

def main():
    # Print ASCII art
    print_ascii_art()

    parser = argparse.ArgumentParser(description="Check live or dead links in media files using HTTP requests.")
    parser.add_argument(
        "-i", "--input", required=False, default="m3u8_dump",
        help="Input folder or file containing media files (default: 'm3u8_dump')."
    )
    parser.add_argument(
        "-o", "--output", required=False, default="m3u8_live",
        help="Output folder to save processed files (default: 'm3u8_live')."
    )
    parser.add_argument(
        "-t", "--threads", type=int, default=10, help="Number of threads to use (default: 10)."
    )
    parser.add_argument(
        "-f", "--file", action="store_true", help="Process a single file instead of a folder."
    )
    parser.add_argument(
        "--timeout", type=int, default=5, help="Timeout for URL checks in seconds (default: 5)."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output."
    )
    parser.add_argument(
        "--retries", type=int, default=3, help="Number of retries for failed URLs (default: 3)."
    )
    parser.add_argument(
        "--extensions", nargs="+", default=[".m3u", ".m3u8", ".mpd", ".mp4"],
        help="File extensions to process (default: .m3u, .m3u8, .mpd, .mp4)."
    )
    parser.add_argument(
        "--combine", action="store_true", help="Combine all .m3u8 files in the output folder into a single playlist."
    )

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output
    max_workers = args.threads
    timeout = args.timeout
    verbose = args.verbose
    retries = args.retries
    extensions = args.extensions

    if args.file:
        # Process a single file
        if not os.path.isfile(input_path):
            print(f"Error: {input_path} is not a valid file.")
            return
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_file = os.path.join(output_path, f"live_{os.path.basename(input_path)}")
        check_streams(input_path, output_file, max_workers, timeout, verbose, retries)
    else:
        # Process all files in a folder
        if not os.path.isdir(input_path):
            print(f"Error: {input_path} is not a valid folder.")
            return
        process_folder(input_path, output_path, max_workers, timeout, verbose, retries, extensions)

    # Combine all .m3u8 files if --combine is specified
    if args.combine:
        combined_file = os.path.join(os.getcwd(), "combined_playlist.m3u8")  # Save in the main directory
        combine_m3u8_files(output_path, combined_file)

if __name__ == "__main__":
    main()