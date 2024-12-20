from enum import Enum


class APIProvider(Enum):
    """Supported API providers."""

    GOOGLE = "google"
    OPEN_LIBRARY = "openlibrary"


API_CONFIG = {
    "google": {
        "base_url": "https://www.googleapis.com/books/v1/volumes",
        "calls_per_minute": 60,
    },
    "openlibrary": {
        "base_url": "https://openlibrary.org/search.json",
        "calls_per_minute": 60,
    },
}
