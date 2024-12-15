import logging
import requests
from ratelimit import limits, sleep_and_retry
from typing import Dict, List, Optional

from ..config import API_CONFIG
from ..models.book import BookInfo
from .base import BookAPI

logger = logging.getLogger(__name__)


class GoogleBooksAPI(BookAPI):
    """Google Books API implementation."""

    @sleep_and_retry
    @limits(calls=API_CONFIG["google"]["calls_per_minute"], period=60)
    def search_books(
        self,
        title: str,
        search_type: str = "similar",
        max_results: int = 5,
        lang: str = "en",
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
