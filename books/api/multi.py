"""
Book Search Script

Description:
    A robust script to search books using multiple APIs (Google Books and Open Library).
    Includes detailed error handling, logging, and rate limiting.

Features:
    - Multiple API support (Google Books and Open Library)
    - Searches by title (exact or similar match)
    - Configurable search parameters
    - Detailed error handling and logging
    - Rate limiting to respect API constraints
    - Rich output formatting

Required packages:
    - requests~=2.31.0
    - rich~=13.5.2
    - ratelimit~=2.2.1

Usage:
    1. Install requirements: pip install -r requirements.txt
    2. Run: python book_search.py
    3. Modify SEARCH_CONFIG as needed

Author: tpinto
"""

import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import requests
from ratelimit import limits, sleep_and_retry
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("book_search")
console = Console()


class APIProvider(Enum):
    """Supported API providers."""

    GOOGLE = "google"
    OPEN_LIBRARY = "openlibrary"


# Configuration
SEARCH_CONFIG = {
    "title": "The Lord of the Rings",
    "search_type": "similar",  # "exact" or "similar"
    "max_results": 5,
    "lang": "en",
    "api_provider": APIProvider.GOOGLE,  # or APIProvider.OPEN_LIBRARY
}

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


@dataclass
class BookInfo:
    """Data class to store book information."""

    title: str
    authors: List[str]
    published_date: str
    publisher: str
    page_count: int
    categories: List[str]
    language: str
    preview_link: str


class BookAPI(ABC):
    """Abstract base class for book API implementations."""

    @abstractmethod
    def search_books(
        self, title: str, search_type: str, max_results: int, lang: str
    ) -> Optional[List[BookInfo]]:
        """Search for books using the API."""
        pass

    @abstractmethod
    def process_response(self, Dict) -> List[BookInfo]:
        """Process API response into BookInfo objects."""
        pass


class GoogleBooksAPI(BookAPI):
    """Google Books API implementation."""

    @sleep_and_retry
    @limits(calls=API_CONFIG["google"]["calls_per_minute"], period=60)
    def search_books(
        self, title: str, search_type: str, max_results: int, lang: str
    ) -> Optional[List[BookInfo]]:
        """Searches for books using the Google Books API.

        Args:
            title (str): The title of the book to search for.
            search_type (str): The type of search, "exact" or "similar".
            max_results (int): The maximum number of results to return.
            lang (str): The language to restrict the results to.

        Returns:
            Optional[List[BookInfo]]: A list of BookInfo objects or None if no books are found or an error occurs.
        """
        params = {
            "q": f'intitle:"{title}"' if search_type == "exact" else title,
            "maxResults": max_results,
            "langRestrict": lang,
        }

        try:
            response = requests.get(
                API_CONFIG["google"]["base_url"], params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if "items" not in data:
                logger.warning("No books found matching the criteria.")
                return None

            return self.process_response(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Google Books API request failed: {str(e)}")

        return None

    def process_response(self, data: Dict) -> List[BookInfo]:
        """Processes the Google Books API response into a list of BookInfo objects.

        Args:
            data (Dict): The JSON response from the Google Books API.

        Returns:
            List[BookInfo]: A list of BookInfo objects.
        """
        books = []
        for item in data["items"]:
            volume_info = item["volumeInfo"]
            books.append(
                BookInfo(
                    title=volume_info.get("title", "Title not available"),
                    authors=volume_info.get("authors", ["Author not available"]),
                    published_date=volume_info.get(
                        "publishedDate", "Date not available"
                    ),
                    publisher=volume_info.get("publisher", "Publisher not available"),
                    page_count=volume_info.get("pageCount", 0),
                    categories=volume_info.get(
                        "categories", ["Category not available"]
                    ),
                    language=volume_info.get("language", "Language not available"),
                    preview_link=volume_info.get("previewLink", "Link not available"),
                )
            )
        return books


class OpenLibraryAPI(BookAPI):
    """Open Library API implementation."""

    @sleep_and_retry
    @limits(calls=API_CONFIG["openlibrary"]["calls_per_minute"], period=60)
    def search_books(
        self, title: str, search_type: str, max_results: int, lang: str
    ) -> Optional[List[BookInfo]]:
        """Searches for books using the Open Library API.

        Args:
            title (str): The title of the book to search for.
            search_type (str): The type of search, this is not used for openlibrary api.
            max_results (int): The maximum number of results to return.
            lang (str): The language to restrict the results to.

        Returns:
            Optional[List[BookInfo]]: A list of BookInfo objects or None if no books are found or an error occurs.
        """
        params = {
            "title": title,
            "limit": max_results,
        }
        if lang == "en":
            params["language"] = "eng"

        try:
            response = requests.get(
                API_CONFIG["openlibrary"]["base_url"], params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("docs"):
                logger.warning("No books found matching the criteria.")
                return None

            return self.process_response(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Open Library API request failed: {str(e)}")

        return None

    def process_response(self, data: Dict) -> List[BookInfo]:
        """Processes the Open Library API response into a list of BookInfo objects.

        Args:
            data (Dict): The JSON response from the Open Library API.

        Returns:
            List[BookInfo]: A list of BookInfo objects.
        """
        books = []
        for doc in data["docs"][: SEARCH_CONFIG["max_results"]]:
            books.append(
                BookInfo(
                    title=doc.get("title", "Title not available"),
                    authors=doc.get("author_name", ["Author not available"]),
                    published_date=str(
                        doc.get("first_publish_year", "Date not available")
                    ),
                    publisher=doc.get("publisher", ["Publisher not available"])[0]
                    if doc.get("publisher")
                    else "Publisher not available",
                    page_count=doc.get("number_of_pages_median", 0),
                    categories=doc.get("subject", ["Category not available"]),
                    language=doc.get("language", ["Language not available"])[0]
                    if doc.get("language")
                    else "Language not available",
                    preview_link=f"https://openlibrary.org{doc.get('key', '')}"
                    if doc.get("key")
                    else "Link not available",
                )
            )
        return books


def get_api_client(provider: APIProvider) -> BookAPI:
    """Factory function to get the appropriate API client.

    Args:
        provider (APIProvider): The API provider to use.

    Returns:
        BookAPI: An instance of the API client.
    """
    api_clients = {
        APIProvider.GOOGLE: GoogleBooksAPI,
        APIProvider.OPEN_LIBRARY: OpenLibraryAPI,
    }
    return api_clients[provider]()


def create_results_table(books: List[BookInfo]) -> Table:
    """Creates a formatted table of book results.

    Args:
        books (List[BookInfo]): A list of BookInfo objects.

    Returns:
        Table: A rich table containing the book information.
    """
    table = Table(title="Search Results", show_lines=True)

    # Add columns
    table.add_column("Title", style="cyan", no_wrap=False)
    table.add_column("Authors", style="green")
    table.add_column("Published", style="yellow")
    table.add_column("Publisher", style="blue")
    table.add_column("Pages", style="magenta")
    table.add_column("Preview Link", style="red")

    # Add rows
    for book in books:
        table.add_row(
            book.title,
            "\n".join(book.authors),
            book.published_date,
            book.publisher,
            str(book.page_count),
            book.preview_link,
        )

    return table


def main() -> None:
    """Main execution function."""
    start_time = datetime.now()
    logger.info(
        f"Starting book search using {SEARCH_CONFIG['api_provider'].value} API..."
    )

    try:
        # Get appropriate API client
        api_client = get_api_client(SEARCH_CONFIG["api_provider"])

        # Perform search
        books = api_client.search_books(
            SEARCH_CONFIG["title"],
            SEARCH_CONFIG["search_type"],
            SEARCH_CONFIG["max_results"],
            SEARCH_CONFIG["lang"],
        )

        if not books:
            logger.error("Search returned no results.")
            sys.exit(1)

        # Display results
        table = create_results_table(books)
        console.print("\n")
        console.print(table)

        # Print summary
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Search completed in {execution_time:.2f} seconds")
        logger.info(f"Found {len(books)} books matching the criteria")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise
        sys.exit(1)


if __name__ == "__main__":
    main()
