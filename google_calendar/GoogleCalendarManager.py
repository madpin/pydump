"""
Note:
    Description: A comprehensive script to manage Google Calendar events, including creation,
                 updating, deletion, sharing, and listing of events and calendars. It supports
                 timezone handling and OAuth2 or Service Account authentication.

    Features:
        - Create, update, and delete Google Calendar events.
        - Retrieve events with filtering by date or maximum number of results.
        - Share calendars with specific users and manage their access levels.
        - List all accessible calendars and their details.
        - Create and delete calendars.
        - Comprehensive timezone support using the pytz library.
        - OAuth2 and Service Account authentication for secure access to the Google Calendar API.
        - Detailed logging for monitoring and debugging.
        - Robust error handling for API interactions.

    Required Environment Variables:
        None. The script uses either a credentials file for OAuth2 authentication or a service
        account file for Service Account authentication.

    Required Packages:
        - google-auth
        - google-auth-oauthlib
        - google-api-python-client
        - pytz

        Install them using pip:
        pip install google-auth google-auth-oauthlib google-api-python-client pytz

    Usage:
        1. Configure Authentication:
           - For OAuth2:
             - Obtain a `credentials.json` file from the Google Cloud Console.
             - Specify the path to this file in the `credentials_file` parameter when
               initializing `GoogleCalendarManager`.
           - For Service Account:
             - Obtain a service account key file (e.g., `service_account.json`) from the
               Google Cloud Console.
             - Specify the path to this file in the `service_account_file` parameter when
               initializing `GoogleCalendarManager`.
        2. Initialize the Manager:
           calendar_manager = GoogleCalendarManager(
               credentials_file='path/to/credentials.json',  # For OAuth2
               # OR
               service_account_file='path/to/service_account.json',  # For Service Account
               calendar_id='your_calendar_id'  # Optional: Specify a default calendar ID
           )
        3. Example Operations:
           # Create an event
           start_time = datetime.now(pytz.timezone('America/New_York')) + timedelta(hours=1)
           end_time = start_time + timedelta(hours=1)
           event = calendar_manager.create_event(
               summary='Meeting',
               start_time=start_time,
               end_time=end_time,
               timezone='America/New_York'
           )

           # Update an event
           calendar_manager.update_event(event_id='your_event_id', summary='Updated Meeting Title')

           # Delete an event
           calendar_manager.delete_event(event_id='your_event_id')

           # List events
           events = calendar_manager.get_events_limit(max_results=10)
           for event in events:
               print(event['summary'])

           # Share a calendar
           calendar_manager.share_calendar(email='user@example.com', role='reader')

           # List calendars
           calendars = calendar_manager.list_calendars()
           for calendar in calendars:
               print(calendar['summary'])

        4. Run the script:
           python your_script_name.py

    Author: tpinto
"""

from datetime import datetime, timedelta
import os
from typing import List, Optional, Dict, Any
import logging
import pytz

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

# Constants
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_SHARING_BASE_URL = (
    "https://calendar.google.com/calendar/u/0/r/settings/calendar"
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleCalendarManager:
    """
    A class to manage Google Calendar events with comprehensive timezone support
    and enhanced error handling.
    """

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        service_account_file: Optional[str] = None,
        token_file: Optional[str] = "token.json",
        calendar_id: str = "primary",
    ) -> None:
        """
        Initializes the calendar manager.

        Args:
            credentials_file: Path to the Google Calendar API credentials file.
            service_account_file: Path to the service account credentials file.
            token_file: Path to store/retrieve OAuth2 tokens.
            calendar_id: Default calendar ID to use for operations (default: "primary").
        """
        self.credentials_file = credentials_file
        self.service_account_file = service_account_file
        self.token_file = token_file
        self.calendar_id = calendar_id
        self.service = self._authenticate()

    def _authenticate(self) -> Any:
        """
        Authenticates with Google Calendar API using OAuth 2.0 or Service Account.

        Returns:
            The Google Calendar API service.

        Raises:
            FileNotFoundError: If credentials file is missing.
            ValueError: If authentication fails.
        """
        creds = None
        try:
            if self.service_account_file:
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=SCOPES
                )
            else:
                if os.path.exists(self.token_file):
                    creds = Credentials.from_authorized_user_file(
                        self.token_file, SCOPES
                    )
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    with open(self.token_file, "w") as token:
                        token.write(creds.to_json())

            return build("calendar", "v3", credentials=creds)
        except FileNotFoundError:
            logger.error(f"Credentials file not found: {self.credentials_file}")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise ValueError("Failed to authenticate with Google Calendar API")

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new calendar event.

        Args:
            summary: Event title.
            start_time: Event start datetime.
            end_time: Event end datetime.
            timezone: Timezone for the event.
            description: Optional event description.
            location: Optional event location.
            attendees: Optional list of attendee email addresses.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            Dict containing the created event details or None if creation failed.

        Raises:
            ValueError: If timezone is invalid or end time is before start time.
        """
        self._validate_event_parameters(timezone, start_time, end_time)

        event_body = self._build_event_body(
            summary, start_time, end_time, timezone, description, location, attendees
        )

        try:
            created_event = (
                self.service.events()
                .insert(calendarId=calendar_id or self.calendar_id, body=event_body)
                .execute()
            )
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timezone: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates an existing calendar event.

        Args:
            event_id: The ID of the event to update.
            summary: Optional new event title.
            start_time: Optional new start datetime.
            end_time: Optional new end datetime.
            timezone: Optional new timezone.
            description: Optional new description.
            location: Optional new location.
            attendees: Optional new list of attendee email addresses.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            Dict containing the updated event details or None if update failed.

        Raises:
            ValueError: If event ID is empty, timezone is invalid, or end time is before start time.
        """
        if not event_id:
            raise ValueError("Event ID cannot be empty")

        cal_id = calendar_id or self.calendar_id

        try:
            event = (
                self.service.events().get(calendarId=cal_id, eventId=event_id).execute()
            )
        except HttpError as error:
            logger.error(f"Error retrieving event: {error}")
            return None

        if timezone:
            self._validate_timezone(timezone)

        if start_time and end_time:
            self._validate_time_range(start_time, end_time)

        # Only update fields that have changed
        update_needed = self._update_event_fields(
            event,
            summary,
            start_time,
            end_time,
            timezone,
            description,
            location,
            attendees,
        )

        if not update_needed:
            logger.info("No changes detected, skipping update.")
            return event

        try:
            updated_event = (
                self.service.events()
                .update(calendarId=cal_id, eventId=event_id, body=event)
                .execute()
            )
            logger.info(f"Event updated: {updated_event.get('htmlLink')}")
            return updated_event
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

    def delete_event(self, event_id: str, calendar_id: Optional[str] = None) -> bool:
        """
        Deletes a calendar event.

        Args:
            event_id: The ID of the event to delete.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            True if deletion was successful, False otherwise.

        Raises:
            ValueError: If event ID is empty.
        """
        if not event_id:
            raise ValueError("Event ID cannot be empty")

        try:
            self.service.events().delete(
                calendarId=calendar_id or self.calendar_id, eventId=event_id
            ).execute()
            logger.info(f"Event deleted: {event_id}")
            return True
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return False

    def get_events_limit(
        self, max_results: int = 10, calendar_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves events from the calendar.

        Args:
            max_results: Maximum number of events to retrieve.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            List of event dictionaries or None if there was an error.
        """
        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id or self.calendar_id,
                    timeMin=datetime.utcnow().isoformat() + "Z",
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return events_result.get("items", [])
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

    def get_events_date(
        self, date: datetime, calendar_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves events from the calendar for a specific date.

        Args:
            date: The date to retrieve events for.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            List of event dictionaries or None if there was an error.
        """
        try:
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())

            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id or self.calendar_id,
                    timeMin=start_datetime.isoformat() + "Z",
                    timeMax=end_datetime.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return events_result.get("items", [])
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return None

    def share_calendar(
        self, email: str, calendar_id: Optional[str] = None, role: str = "reader"
    ) -> bool:
        """
        Shares the calendar with a user.

        Args:
            email: Email address of the user to share with.
            calendar_id: Optional calendar ID (uses default if not provided).
            role: Access role to grant (default: "reader").

        Returns:
            True if sharing was successful, False otherwise.
        """
        rule = {
            "scope": {"type": "user", "value": email},
            "role": role,
        }

        try:
            self.service.acl().insert(
                calendarId=calendar_id or self.calendar_id, body=rule
            ).execute()
            logger.info(f"Successfully shared calendar with {email} (role: {role})")
            return True
        except HttpError as error:
            logger.error(f"Failed to share calendar: {error}")
            return False

    def list_shared_users(
        self, calendar_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists all users who have access to the calendar.

        Args:
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            List of access control rules.
        """
        try:
            acl = (
                self.service.acl()
                .list(calendarId=calendar_id or self.calendar_id)
                .execute()
            )
            return acl.get("items", [])
        except HttpError as error:
            logger.error(f"Failed to list shared users: {error}")
            return []

    def remove_calendar_access(
        self, email: str, calendar_id: Optional[str] = None
    ) -> bool:
        """
        Removes calendar access for a specific user.

        Args:
            email: The email address of the user to remove access for.
            calendar_id: Optional calendar ID (uses default if not provided).

        Returns:
            True if removal was successful, False otherwise.
        """
        try:
            rule_id = f"user:{email}"
            self.service.acl().delete(
                calendarId=calendar_id or self.calendar_id, ruleId=rule_id
            ).execute()
            logger.info(f"Successfully removed calendar access for {email}")
            return True
        except HttpError as error:
            logger.error(f"Failed to remove calendar access: {error}")
            return False

    def create_calendar(
        self, summary: str, description: Optional[str] = None, timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Creates a new Google Calendar.

        Args:
            summary: Calendar name.
            description: Optional calendar description.
            timezone: Calendar timezone (default: UTC).

        Returns:
            Created calendar object.
        """
        calendar_body = {"summary": summary, "timeZone": timezone}
        if description:
            calendar_body["description"] = description

        try:
            calendar = self.service.calendars().insert(body=calendar_body).execute()
            logger.info(f"Created calendar: {summary}")
            logger.info(f"Calendar ID: {calendar['id']}")
            if not self.calendar_id:
                self.calendar_id = calendar["id"]
            return calendar
        except HttpError as error:
            logger.error(f"Failed to create calendar: {error}")
            return {}

    def delete_calendar(self, calendar_id: Optional[str] = None) -> bool:
        """
        Deletes a Google Calendar.

        Args:
            calendar_id: Optional ID of calendar to delete.
                         If not provided, uses the instance's calendar_id.

        Returns:
            True if deletion was successful, False otherwise.
        """
        cal_id = calendar_id or self.calendar_id
        if not cal_id:
            logger.warning("No calendar ID provided")
            return False

        try:
            self.service.calendars().delete(calendarId=cal_id).execute()
            logger.info(f"Successfully deleted calendar: {cal_id}")
            if cal_id == self.calendar_id:
                self.calendar_id = None
            return True
        except HttpError as error:
            logger.error(f"Failed to delete calendar: {error}")
            return False

    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        Lists all calendars available to the service account.

        Returns:
            List of calendar objects.
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            if not calendars:
                logger.info("No calendars found")
            else:
                logger.info("\nAvailable Calendars:")
                for calendar in calendars:
                    logger.info(f"- {calendar['summary']} (ID: {calendar['id']})")
            return calendars
        except HttpError as error:
            logger.error(f"Failed to list calendars: {error}")
            return []

    def get_calendar_details(self, calendar_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets detailed information about a specific calendar.

        Args:
            calendar_id: Optional ID of calendar to get details for.
                         If not provided, uses the instance's calendar_id.

        Returns:
            Calendar details object.
        """
        cal_id = calendar_id or self.calendar_id
        if not cal_id:
            logger.warning("No calendar ID provided")
            return {}

        try:
            return self.service.calendars().get(calendarId=cal_id).execute()
        except HttpError as error:
            logger.error(f"Failed to get calendar details: {error}")
            return {}

    def _build_event_body(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Helper method to build the event body for API requests, including timezone information.

        Args:
            summary: Event title.
            start_time: Event start datetime (timezone-aware or naive).
            end_time: Event end datetime (timezone-aware or naive).
            timezone: Timezone for the event (e.g., 'America/New_York').
            description: Optional event description.
            location: Optional event location.
            attendees: Optional list of attendee email addresses.

        Returns:
            Dict containing the formatted event body for API request.
        """
        event_body = {
            "summary": summary,
            "start": {
                "dateTime": self._format_datetime(start_time, timezone),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": self._format_datetime(end_time, timezone),
                "timeZone": timezone,
            },
        }
        if description is not None:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": attendee} for attendee in attendees]

        return event_body

    def _format_datetime(self, dt: datetime, timezone: str) -> str:
        """
        Formats a datetime object into a string representation for the Google Calendar API,
        handling timezone conversions if necessary.

        Args:
            dt: The datetime object.
            timezone: The target timezone.

        Returns:
            A string representation of the datetime in ISO 8601 format with timezone offset.
        """
        if dt.tzinfo is None:
            tz = pytz.timezone(timezone)
            dt = tz.localize(dt)
        else:
            tz = pytz.timezone(timezone)
            dt = dt.astimezone(tz)

        return dt.isoformat()

    def _validate_timezone(self, timezone_str: str) -> None:
        """
        Validates a timezone string using the pytz library.

        Args:
            timezone_str: The timezone string to validate.

        Raises:
            ValueError: If the timezone is invalid.
        """
        try:
            pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone_str}")

    def _validate_time_range(self, start_time: datetime, end_time: datetime) -> None:
        """
        Validates that the end time is not before the start time.

        Args:
            start_time: The start datetime.
            end_time: The end datetime.

        Raises:
            ValueError: If end time is before start time.
        """
        if end_time < start_time:
            raise ValueError("End time cannot be before start time")

    def _validate_event_parameters(
        self, timezone: str, start_time: datetime, end_time: datetime
    ) -> None:
        """
        Validates event parameters.

        Args:
            timezone: The timezone string.
            start_time: The start datetime.
            end_time: The end datetime.

        Raises:
            ValueError: If timezone is invalid or end time is before start time.
        """
        self._validate_timezone(timezone)
        self._validate_time_range(start_time, end_time)

    def _update_event_fields(
        self,
        event: Dict[str, Any],
        summary: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        timezone: Optional[str],
        description: Optional[str],
        location: Optional[str],
        attendees: Optional[List[str]],
    ) -> bool:
        """
        Updates the event dictionary with new values for specified fields.

        Args:
            event: The event dictionary to update.
            summary: Optional new event title.
            start_time: Optional new start datetime.
            end_time: Optional new end datetime.
            timezone: Optional new timezone.
            description: Optional new description.
            location: Optional new location.
            attendees: Optional new list of attendee email addresses.

        Returns:
            True if any fields were updated, False otherwise.
        """
        update_needed = False
        if summary is not None and event.get("summary") != summary:
            event["summary"] = summary
            update_needed = True
        if start_time is not None and self._format_datetime(
            start_time, timezone or event["start"].get("timeZone")
        ) != event["start"].get("dateTime"):
            event["start"] = {
                "dateTime": self._format_datetime(
                    start_time, timezone or event["start"].get("timeZone")
                ),
                "timeZone": timezone or event["start"].get("timeZone"),
            }
            update_needed = True
        if end_time is not None and self._format_datetime(
            end_time, timezone or event["end"].get("timeZone")
        ) != event["end"].get("dateTime"):
            event["end"] = {
                "dateTime": self._format_datetime(
                    end_time, timezone or event["end"].get("timeZone")
                ),
                "timeZone": timezone or event["end"].get("timeZone"),
            }
            update_needed = True
        if description is not None and event.get("description") != description:
            event["description"] = description
            update_needed = True
        if location is not None and event.get("location") != location:
            event["location"] = location
            update_needed = True
        if attendees is not None:
            current_attendees = {
                a["email"] for a in event.get("attendees", []) if "email" in a
            }
            new_attendees = set(attendees)
            if current_attendees != new_attendees:
                event["attendees"] = [{"email": attendee} for attendee in attendees]
                update_needed = True

        return update_needed


if __name__ == "__main__":
    """
    Main execution block for testing and demonstrating the GoogleCalendarManager class.
    """
    calendar_manager = GoogleCalendarManager(
        # credentials_file="credentials2.json",
        service_account_file="madpin-14bd25c3d9fa.json",
        # calendar_id="c0a0fb92528d12044eb6dae243e92a8c595619161e0d064d1fd67073e99ef027@group.calendar.google.com",
    )

    calendars = calendar_manager.list_calendars()
    if calendars:
        calendar_manager.calendar_id = calendars[0]["id"]
    else:
        created_calendar = calendar_manager.create_calendar("test calendar")
        calendar_manager.calendar_id = created_calendar["id"]

    start_time = datetime.now(pytz.timezone("America/New_York")) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)
    event = calendar_manager.create_event(
        summary="Dummy Event",
        description="This is a test event",
        start_time=start_time,
        end_time=end_time,
        timezone="America/New_York",
    )

    logger.info("#########################################################")
    logger.info(calendar_manager.get_calendar_details())
    logger.info("#########################################################")
    users = calendar_manager.list_shared_users()
    for user in users:
        logger.info(user["scope"]["value"])
    logger.info("#########################################################")
