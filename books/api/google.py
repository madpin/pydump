"""
Google Books Search Script

Description: 
    A robust script to search the Google Books API for books based on title.
    Includes detailed error handling, logging, and rate limiting.

Features:
    - Searches Google Books API by title (exact or similar match)
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
from dataclasses import dataclass
from datetime import datetime
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
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("book_search")
console = Console()

# Configuration
SEARCH_CONFIG = {
    "title": "The Lord of the Rings",
    "search_type": "similar",  # "exact" or "similar"
    "max_results": 5,
    "lang": "en"
}

API_CONFIG = {
    "base_url": "https://www.googleapis.com/books/v1/volumes",
    "calls_per_minute": 60,  # Google Books API limit
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

    @classmethod
    def from_api_response(cls, volume_info: Dict) -> 'BookInfo':
        """Creates a BookInfo instance from API response data."""
        return cls(
            title=volume_info.get("title", "Title not available"),
            authors=volume_info.get("authors", ["Author not available"]),
            published_date=volume_info.get("publishedDate", "Date not available"),
            publisher=volume_info.get("publisher", "Publisher not available"),
            page_count=volume_info.get("pageCount", 0),
            categories=volume_info.get("categories", ["Category not available"]),
            language=volume_info.get("language", "Language not available"),
            preview_link=volume_info.get("previewLink", "Link not available")
        )

@sleep_and_retry
@limits(calls=API_CONFIG["calls_per_minute"], period=60)
def search_google_books(
    title: str,
    search_type: str,
    max_results: int,
    lang: str
) -> Optional[List[Dict]]:
    """
    Search Google Books API with rate limiting and error handling.

    Args:
        title: Book title to search for
        search_type: Type of search ("exact" or "similar")
        max_results: Maximum number of results to return
        lang: Language code for results filtering

    Returns:
        List of book data dictionaries or None if error occurs
    """
    params = {
        "q": f'intitle:"{title}"' if search_type == "exact" else title,
        "maxResults": max_results,
        "langRestrict": lang
    }

    try:
        response = requests.get(
            API_CONFIG["base_url"],
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if "items" not in data:
            logger.warning("No books found matching the criteria.")
            return None
            
        return data["items"]

    except requests.exceptions.Timeout:
        logger.error("Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
    except ValueError as e:
        logger.error(f"Failed to parse API response: {str(e)}")
    
    return None

def create_results_table(books: List[BookInfo]) -> Table:
    """Creates a formatted table of book results."""
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
            book.preview_link
        )

    return table

def main() -> None:
    """Main execution function."""
    start_time = datetime.now()
    logger.info("Starting book search...")

    try:
        # Perform search
        results = search_google_books(
            SEARCH_CONFIG["title"],
            SEARCH_CONFIG["search_type"],
            SEARCH_CONFIG["max_results"],
            SEARCH_CONFIG["lang"]
        )

        if not results:
            logger.error("Search returned no results.")
            sys.exit(1)

        # Process results
        books = [
            BookInfo.from_api_response(item["volumeInfo"])
            for item in results
        ]

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
        sys.exit(1)

if __name__ == "__main__":
    main()
