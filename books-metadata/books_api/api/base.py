from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from ..models.book import BookInfo


class BookAPI(ABC):
    """Abstract base class for book API implementations."""

    @abstractmethod
    def search_books(
        self,
        title: str,
        search_type: str = "similar",
        max_results: int = 5,
        lang: str = "en",
    ) -> Optional[List[BookInfo]]:
        """Search for books using the API."""
        pass

    @abstractmethod
    def process_response(self, data: Dict) -> List[BookInfo]:
        """Process API response into BookInfo objects."""
        pass
