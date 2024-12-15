from dataclasses import dataclass
from typing import List


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
