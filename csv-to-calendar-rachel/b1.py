"""
Description: This script processes a spreadsheet containing rota information and generates a CSV file
             for Rachel's schedule in Google Calendar format, handling overnight shifts correctly.

Features:
- Extracts Rachel's schedule from the input data
- Converts the schedule to Google Calendar CSV format
- Handles different shift types, including overnight shifts
- Deals with various date and time formats

Required packages:
- csv
- datetime

Usage:
python rachel_schedule_to_csv.py

Author: tpinto
"""

import csv
from datetime import datetime, timedelta
from typing import Dict, List
import re

# Constants
INPUT_FILE = "./data/rota.csv"
OUTPUT_FILE = "rota_rachel_calendar.csv"
DATE_FORMAT = "%d %b"  # e.g. "01 Jan", "25 Dec" - day followed by abbreviated month nameTIME_FORMAT = "%H%M"
TIME_FORMAT = "%H%M"
CALENDAR_DATE_FORMAT = "%m/%d/%Y"
CALENDAR_TIME_FORMAT = "%I:%M %p"
ALL_DAY_EVENTS = {
    "AL",
    "SL",
    "NCD",
    "ICU",
    "PL",
}

SKIP_EVENTS = {"/", "OFF", "Post nights", "Post Nights", "PRE NIGHT OFF"}


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object, handling various date formats."""
    date_str = date_str.strip()
    
    # Try standard format first
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        # Try alternative formats
        formats = [
            "%d-%b",     # 01-Jan
            "%d/%b",     # 01/Jan
            "%d %B",     # 01 January
            "%d-%B",     # 01-January
            "%d/%B",     # 01/January
            "%b %d",     # Jan 01
            "%B %d",     # January 01
            "%a %d %b",  # Mon 23 Dec
            "%A %d %b",  # Monday 23 Dec
            "%a %d %B",  # Mon 23 December
            "%A %d %B"   # Monday 23 December
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # If all formats fail, raise error
        raise ValueError(f"Unable to parse date string: {date_str}")


def parse_time(time_str: str) -> datetime:
    """Parse time string to datetime object."""
    # Remove decimal part if present
    time_str = time_str.split(".")[0]
    return datetime.strptime(time_str, TIME_FORMAT)


def format_date(dt: datetime) -> str:
    """Format datetime object to date string for Google Calendar."""
    return dt.strftime(CALENDAR_DATE_FORMAT)


def format_time(dt: datetime) -> str:
    """Format datetime object to time string for Google Calendar."""
    return dt.strftime(CALENDAR_TIME_FORMAT)


def extract_times_from_shift(shift: str) -> tuple:
    """Extract start and end times from shift string, handling various formats."""
    if "(" in shift and ")" in shift:
        # Extract time from format like "Zone 2 (8-6pm)"
        time_part = re.search(r"\((.*?)\)", shift).group(1)
        if "am" in time_part.lower() or "pm" in time_part.lower():
            # Convert 12-hour format to 24-hour
            times = time_part.replace("am", "").replace("pm", "").split("-")
            start_hour = int(times[0])
            end_hour = int(times[1].replace("pm", ""))
            if "pm" in time_part.lower() and end_hour != 12:
                end_hour += 12
            return f"{start_hour:02d}00", f"{end_hour:02d}00"
    elif "-" in shift:
        times = shift.split("-")
        return times[0].strip(), times[1].strip()
    return "0800", "1800"  # Default times


def process_shift(date: datetime, shift: str) -> Dict[str, str]:
    """Process shift information and return event details."""
    if shift in SKIP_EVENTS:
        return None

    if shift in ALL_DAY_EVENTS:
        return {
            "Subject": f"Rachel - {shift}",
            "Start Date": format_date(date),
            "Start Time": "",
            "End Date": format_date(date + timedelta(days=1)),
            "End Time": "",
            "All Day Event": "True",
            "Description": f"Shift: {shift}",
            "Location": "",
            "Private": "False",
        }

    start_time, end_time = extract_times_from_shift(shift)

    start_dt = date.replace(
        hour=parse_time(start_time).hour, minute=parse_time(start_time).minute
    )
    end_dt = date.replace(
        hour=parse_time(end_time).hour, minute=parse_time(end_time).minute
    )

    # Handle overnight shifts
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    return {
        "Subject": "Rachel - Work",
        "Start Date": format_date(start_dt),
        "Start Time": format_time(start_dt),
        "End Date": format_date(end_dt),
        "End Time": format_time(end_dt),
        "All Day Event": "False",
        "Description": f"Shift: {shift}",
        "Location": "",
        "Private": "False",
    }


def read_rota_file(filename: str) -> List[Dict[str, str]]:
    """Read the rota file and extract Rachel's schedule."""
    rachel_schedule = []
    current_week = None
    current_year = datetime.now().year
    current_month = datetime.now().month

    with open(filename, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                if row and row[0] in ["SHO", "REG"]:
                    current_week = row[1]
                elif current_week and row and len(row) > 1 and row[1] == "Rachel":
                    if len(row) < 3 or not row[2]:
                        continue

                    # Use a default date (1st of current month) when date cannot be extracted
                    date = datetime(current_year, current_month, 1)

                    for i, shift in enumerate(row[2:9]):
                        if shift:  # Only process non-empty shifts
                            event_date = date + timedelta(days=i)
                            event = process_shift(event_date, shift)
                            if event:
                                rachel_schedule.append(event)
            except Exception:
                print(f"\nError processing row: \n\n{row}")
                raise

    return rachel_schedule


def write_calendar_file(filename: str, events: List[Dict[str, str]]) -> None:
    """Write the calendar events to a CSV file."""
    fieldnames = [
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
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)


def main():
    rachel_schedule = read_rota_file(INPUT_FILE)
    write_calendar_file(OUTPUT_FILE, rachel_schedule)
    print(f"Rachel's schedule has been successfully exported to '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
