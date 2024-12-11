"""
Description: This script processes a CSV file containing work schedules and generates a Google Calendar CSV file for a specific person.

Features:
- Reads a complex CSV file with multiple "mini tables"
- Extracts schedule information for a specific person
- Handles all-day events and skip events
- Processes various time formats including "Zone" formats and overnight shifts
- Generates a Google Calendar compatible CSV file

Required packages:
- csv
- datetime
- re

Usage:
python process_schedule.py <input_csv_file> <output_csv_file>

Author: tpinto
"""

import csv
from datetime import datetime, timedelta
import sys
import re

# Constants
INPUT_FILE = "./data/rota.csv"
OUTPUT_FILE = "rota_rachel_calendar.csv"
ALL_DAY_EVENTS = {"AL", "SL", "NCD", "ICU", "PL"}
SKIP_EVENTS = {"/", "off", "post nights", "post nights", "pre night off"}


def parse_date(date_str):
    """Parse date string to datetime object."""
    return datetime.strptime(date_str, "%a %d %b")


def parse_time(time_str):
    """Parse time string to datetime object, handling various formats."""
    time_str = time_str.strip().lower()

    # Handle "Zone" format
    zone_match = re.match(r"zone \d+ \((\d+)(?:am|pm)?-(\d+)(am|pm)\)", time_str)
    if zone_match:
        start, end, end_period = zone_match.groups()
        start = int(start)
        end = int(end)

        # Adjust start time if necessary
        if end_period == "pm" and end < 12:
            if start > end:
                start_period = "am"
            else:
                start_period = "pm"

            if start_period == "pm" and start < 12:
                start += 12

        # Adjust end time
        if end_period == "pm" and end < 12:
            end += 12

        return datetime.strptime(f"{start:02d}:00", "%H:%M"), datetime.strptime(
            f"{end:02d}:00", "%H:%M"
        )

    # Handle "HH.MM - HH.MM" format
    time_range_match = re.match(r"(\d{2})\.(\d{2})\s*-\s*(\d{2})\.(\d{2})", time_str)
    if time_range_match:
        start_h, start_m, end_h, end_m = map(int, time_range_match.groups())
        return datetime.strptime(
            f"{start_h:02d}:{start_m:02d}", "%H:%M"
        ), datetime.strptime(f"{end_h:02d}:{end_m:02d}", "%H:%M")

    # Handle "HHMM-HHMM" format
    simple_range_match = re.match(r"(\d{4})-(\d{4})", time_str)
    if simple_range_match:
        start, end = simple_range_match.groups()
        return datetime.strptime(start, "%H%M"), datetime.strptime(end, "%H%M")

    raise ValueError(f"Unrecognized time format: {time_str}")


def process_csv(input_file, output_file, target_name="Rachel"):
    with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        writer.writerow(
            [
                "Subject",
                "Start Date",
                "Start Time",
                "End Date",
                "End Time",
                "All Day Event",
                "Description",
                "Location",
                "Private",
            ]
        )

        current_date = None
        current_year = datetime.now().year

        for row in reader:
            if not row:
                continue

            if row[0] in ("REG", "SHO") and row[2].startswith(
                ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
            ):
                current_date = parse_date(row[2]).replace(year=current_year)

            if row[0] == target_name or (len(row) > 1 and row[1] == target_name):
                if not current_date:
                    continue

                for i, cell in enumerate(row[2:9], start=2):
                    if cell.strip().lower() in SKIP_EVENTS:
                        continue

                    event_date = current_date + timedelta(days=i - 2)

                    if cell in ALL_DAY_EVENTS:
                        writer.writerow(
                            [
                                cell,  # Subject
                                event_date.strftime("%m/%d/%Y"),  # Start Date
                                "",  # Start Time
                                event_date.strftime("%m/%d/%Y"),  # End Date
                                "",  # End Time
                                "True",  # All Day Event
                                "",  # Description
                                "",  # Location
                                "False",  # Private
                            ]
                        )
                    elif cell and cell not in ("-", ""):
                        try:
                            start_time, end_time = parse_time(cell)
                            start_datetime = event_date.replace(
                                hour=start_time.hour, minute=start_time.minute
                            )
                            end_datetime = event_date.replace(
                                hour=end_time.hour, minute=end_time.minute
                            )

                            # Handle overnight shifts
                            if end_datetime <= start_datetime:
                                end_datetime += timedelta(days=1)

                            writer.writerow(
                                [
                                    f"Hospital ({start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')})",  # Subject
                                    start_datetime.strftime("%m/%d/%Y"),  # Start Date
                                    start_datetime.strftime("%I:%M %p"),  # Start Time #
                                    end_datetime.strftime("%m/%d/%Y"),  # End Date
                                    end_datetime.strftime("%I:%M %p"),  # End Time
                                    "False",  # All Day Event
                                    f"Shift: {cell}",  # Description
                                    "",  # Location
                                    "False",  # Private
                                ]
                            )
                        except ValueError as e:
                            print(
                                f"Warning: Unable to process time '{cell}' for date {event_date}: {str(e)}"
                            )


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    output_file = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE
    process_csv(input_file, output_file)
    print(f"Processing complete. Output written to {output_file}")
