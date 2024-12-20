import logging
import requests
from ratelimit import limits, sleep_and_retry
from typing import Dict, List, Optional

from ..config import API_CONFIG
from ..models.book import BookInfo
from .base import BookAPI

logger = logging.getLogger(__name__)


class OpenLibraryAPI(BookAPI):
    """Open Library API implementation."""

    @sleep_and_retry
    @limits(calls=API_CONFIG["openlibrary"]["calls_per_minute"], period=60)
    def search_books(
        self,
        title: str,
        search_type: str = "similar",
        max_results: int = 5,
        lang: str = "en",
    ) -> Optional[List[BookInfo]]:
        """Searches for books using the Open Library API.

        Args:
            title (str): The title of the book to search for.
            search_type (str): The type of search (not used for Open Library).
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
        for doc in data["docs"]:
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
