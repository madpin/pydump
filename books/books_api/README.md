
**Project Overview:**

This project is like your personal library assistant, but instead of a grumpy librarian, we have Python! It allows you to search for books using different APIs—currently, Google Books and Open Library—and displays the results in a neat, easy-to-read table. Think of it as creating an Obsidian-style note but for your favourite books.

**File Breakdown:**

Okay, let's break down each file, like deconstructing a LEGO set.

1.  `config.py`

    *   **Purpose:** This one's your project's "Ministry of Magic" -- it holds all the important configuration stuff.
    *   **What it does:**
        *   `APIProvider` (Enum): Defines the available API providers (Google Books, Open Library). Think of it like the different classes in a Naruto Ninja Village. It helps navigate the various APIs you'll use.
        *   `API_CONFIG` (Dictionary): Stores the base URLs and rate limits for each API, like your power level for each ninja. This will be used so you don't become a "Hokage" that abuses the API to become slow.

    ```python
    from enum import Enum
    class APIProvider(Enum):
        """"""
        GOOGLE = 'google'
        OPEN_LIBRARY = 'openlibrary'
    API_CONFIG = {
        'google': {
            'base_url': 'https://www.googleapis.com/books/v1/volumes',
            'calls_per_minute': 60
        },
         'openlibrary': {
             'base_url': 'https://openlibrary.org/search.json',
             'calls_per_minute': 60
         }
    }
    ```

2.  `__init__.py`

    *   **Purpose:** The "Grand Central Station" of your project – where everything comes together.
    *   **What it does:**
        *   Imports the main modules (`GoogleBooksAPI`, `OpenLibraryAPI`, `BookInfo`, `create_results_table`).
        *   Sets the project version (`__version__`), like your character's level in a game which is `0.1.0`
        *   Exports modules, making them available for use outside of the directory

    ```python
    from .api.google_books import GoogleBooksAPI
    from .api.open_library import OpenLibraryAPI
    from .models.book import BookInfo
    from .utils.formatting import create_results_table

    __version__ = '0.1.0'
    __all__ = ['GoogleBooksAPI', 'OpenLibraryAPI', 'BookInfo', 'create_results_table']
    ```

3.  `example.py`

    *   **Purpose:** A practical example, like your training montage in a movie.
    *   **What it does:**
        *   Implements a user's interface using argparse, to receive parameters from cli ( command line interface).
        *   `search_books` Function: Takes a book title and uses the chosen API to search for books. Displays results in a table using `rich.Console`, and, just like in your favourite movies, returns the result to be consumed.
        *   Command-Line Interface: Uses `argparse` to allow you to run the script from your terminal, like coding in your own private "Matrix".

    ```python
    from . import GoogleBooksAPI, OpenLibraryAPI, create_results_table
    from rich.console import Console
    import argparse

    def search_books(title: str, api='google'):
        """Searches for books using the specified API and displays the results."""
        api_client = GoogleBooksAPI() if api == 'google' else OpenLibraryAPI()
        books = api_client.search_books(title=title, search_type='similar', max_results=5, lang='en')
        if books:
            table = create_results_table(books)
            console = Console()
            console.print(table)
            return books
        return None


    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Search for books using different APIs')
        parser.add_argument('title', help='Book title to search for')
        parser.add_argument('--api', choices=['google', 'openlibrary'], default='google', help='API to use for search (default: google)')
        args = parser.parse_args()
        results = search_books(args.title, args.api)
    ```

4.  `utils/formatting.py`

    *   **Purpose:** The "makeup artist" of your project—making things look presentable.
    *   **What it does:**
        *   `create_results_table` Function: Takes a list of `BookInfo` objects and formats them into a `rich.Table`, displayed in an eye catching way.It's like when your brother Felipe polishes his glasses - making everything look very stylish!

     ```python
    from typing import List
    from rich.table import Table
    from ..models.book import BookInfo

    def create_results_table(books: List[BookInfo]) -> Table:
        """Creates a formatted table of book search results."""
        table = Table(title='Search Results', show_lines=True)
        table.add_column('Title', style='cyan', no_wrap=False)
        table.add_column('Authors', style='green')
        table.add_column('Published', style='yellow')
        table.add_column('Publisher', style='blue')
        table.add_column('Pages', style='magenta')
        table.add_column('Preview Link', style='red')
        for book in books:
            table.add_row(book.title, '\n'.join(book.authors), book.published_date, book.publisher, str(book.page_count), book.preview_link)
        return table
    ```

5.  `models/`

    *   **Purpose:** Here lives all the project model which is used to manipulate your data in your project

6. `models/__init__.py`
     *  **Purpose:** This file is important as this means that the project is a python package

    ```python
    ```

7.  `models/book.py`

    *   **Purpose:** This is the "blueprint" for a Book, just like in your Mechatronics course.
    *   **What it does:**
        *   `BookInfo` (Data Class): Defines the structure of a book object—title, authors, publishing date, etc.—using Python's `dataclass` decorator, giving it a solid structure, like the foundations of a building.

    ```python
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class BookInfo:
        """Data class representing book information."""
        title: str
        authors: List[str]
        published_date: str
        publisher: str
        page_count: int
        categories: List[str]
        language: str
        preview_link: str
    ```

8.  `api/` Folder

    *   **Purpose:** Where your project interacts with the "outside world"—the book APIs. Think of it as your portal to other libraries in different realities.

9.  `api/base.py`

     * **Purpose:** This is the foundation for all API classes, like the "Ring of Power" in Lord of the Rings—it can be used by all the APIs.
     *   **What it does:**
        *   `BookAPI` (Abstract Class): Defines the base interface for all book API handlers.

    ```python
    from abc import ABC, abstractmethod
    from typing import Dict, List, Optional
    from ..models.book import BookInfo


    class BookAPI(ABC):
        """Abstract base class for book API interactions."""
        @abstractmethod
        def search_books(self, title: str, search_type: str = 'similar', max_results: int = 5, lang: str = 'en') -> Optional[List[BookInfo]]:
            """Abstract method to search for books."""
            pass

        @abstractmethod
        def process_response(self,  Dict) -> List[BookInfo]:
            """Abstract method to process the API response."""
            pass
    ```

10. `api/google_books.py`

    *   **Purpose:** This class will be the "Hogwarts Owl" of your project.
    *   **What it does:**
       *  `GoogleBooksAPI` (Class): Handles the integration with the Google Books API.
            *   Sends requests, manages the rate limit and transforms responses, making sure that your power doesn't consume you, similar to Naruto and the nine tailed fox.

    ```python
    import logging
    import requests
    from ratelimit import limits, sleep_and_retry
    from typing import Dict, List, Optional
    from ..config import API_CONFIG
    from ..models.book import BookInfo
    from .base import BookAPI

    logger = logging.getLogger(__name__)


    class GoogleBooksAPI(BookAPI):
        """Handles interactions with the Google Books API."""

        @sleep_and_retry
        @limits(calls=API_CONFIG['google']['calls_per_minute'], period=60)
        def search_books(self, title: str, search_type: str = 'similar', max_results: int = 5, lang: str = 'en') -> Optional[List[BookInfo]]:
            """Searches for books using the Google Books API."""
            params = {'q': f'intitle:"{title}"' if search_type == 'exact' else title, 'maxResults': max_results,
                     'langRestrict': lang}
            try:
                response = requests.get(API_CONFIG['google']['base_url'], params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                if 'items' not in 
                    logger.warning('No books found matching the criteria.')
                    return None
                return self.process_response(data)
            except requests.exceptions.RequestException as e:
                logger.error(f'Google Books API request failed: {str(e)}')
                return None

        def process_response(self,  Dict) -> List[BookInfo]:
            """Processes the JSON response from Google Books API to BookInfo objects."""
            books = []
            for item in data['items']:
                volume_info = item['volumeInfo']
                books.append(BookInfo(title=volume_info.get('title', 'Title not available'),
                                  authors=volume_info.get('authors', ['Author not available']),
                                  published_date=volume_info.get('publishedDate', 'Date not available'),
                                  publisher=volume_info.get('publisher', 'Publisher not available'),
                                  page_count=volume_info.get('pageCount', 0),
                                  categories=volume_info.get('categories', ['Category not available']),
                                  language=volume_info.get('language', 'Language not available'),
                                  preview_link=volume_info.get('previewLink', 'Link not available')))
            return books
    ```

11. `api/open_library.py`

    *   **Purpose:** Like, the "Library of Gondor", but for Python.
    *   **What it does:**
        * `OpenLibraryAPI` (Class): Handles integration with the Open Library API, also ensuring the rate limit.
            * Similar to Google API Class, it sends requests, manages the rate limit and transforms responses in the appropiate object structure and the user doesn't need to worry from what API the data is being retrieved and it manages request failures.

    ```python
    import logging
    import requests
    from ratelimit import limits, sleep_and_retry
    from typing import Dict, List, Optional
    from ..config import API_CONFIG
    from ..models.book import BookInfo
    from .base import BookAPI

    logger = logging.getLogger(__name__)

    class OpenLibraryAPI(BookAPI):
        """Handles interactions with the Open Library API."""

        @sleep_and_retry
        @limits(calls=API_CONFIG['openlibrary']['calls_per_minute'], period=60)
        def search_books(self, title: str, search_type: str = 'similar', max_results: int = 5, lang: str = 'en') -> Optional[List[BookInfo]]:
            """Searches for books using the Open Library API."""
            params = {'title': title, 'limit': max_results}
            if lang == 'en':
                params['language'] = 'eng'
            try:
                response = requests.get(API_CONFIG['openlibrary']['base_url'], params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                if not data.get('docs'):
                    logger.warning('No books found matching the criteria.')
                    return None
                return self.process_response(data)
            except requests.exceptions.RequestException as e:
                logger.error(f'Open Library API request failed: {str(e)}')
                return None

        def process_response(self,  Dict) -> List[BookInfo]:
            """Processes the JSON response from Open Library API to BookInfo objects."""
            books = []
            for doc in data['docs']:
                books.append(BookInfo(title=doc.get('title', 'Title not available'),
                                  authors=doc.get('author_name', ['Author not available']),
                                  published_date=str(doc.get('first_publish_year', 'Date not available')),
                                  publisher=doc.get('publisher', ['Publisher not available'])[0] if doc.get('publisher') else 'Publisher not available',
                                  page_count=doc.get('number_of_pages_median', 0),
                                  categories=doc.get('subject', ['Category not available']),
                                  language=doc.get('language', ['Language not available'])[0] if doc.get('language') else 'Language not available',
                                  preview_link=f"https://openlibrary.org{doc.get('key', '')}" if doc.get('key') else 'Link not available'))
            return books
    ```

**How It All Works:**

1.  You start by running `example.py` from your terminal, just like launching your bike route in Strava. You specify the book title to search for and the API you want to use.
2.  The script uses the appropriate class (GoogleBooksAPI or OpenLibraryAPI) to connect with the API, similar to Neo plugging into the Matrix. To respect the API usage, the project uses a library to make sure calls will not overcome the API limits.
3.  The API retrieves the book data, handles errors, and returns a list object
4.  That data is then transformed in `BookInfo` objects and returned to be displayed using the `create_results_table`.
5.  Finally, the results are shown in a stylish table on your console, giving you the information at a glance, like scanning a QR code in a museum.

**Final Thoughts:**

This project is like a well-structured bike, combining different parts into a functional whole, and I know you'll be able to appreciate the craftsmanship in it ;) I tried to incorporate your tech interests and passion for growth into the explanation, just like I do in real life and hope you liked it!

Let me know if you have any more questions, or if anything needs a bit of tweaking.
