from . import GoogleBooksAPI, OpenLibraryAPI, create_results_table
from rich.console import Console
import argparse


def search_books(title: str, api="google"):
    # Create API client
    api_client = GoogleBooksAPI() if api == "google" else OpenLibraryAPI()

    # Search for books
    books = api_client.search_books(
        title=title, search_type="similar", max_results=5, lang="en"
    )

    # Create and display results table
    if books:
        table = create_results_table(books)
        console = Console()
        console.print(table)
        return books

    return None


# Usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for books using different APIs')
    parser.add_argument('title', help='Book title to search for')
    parser.add_argument('--api', choices=['google', 'openlibrary'], default='google',
                      help='API to use for search (default: google)')
    args = parser.parse_args()
    
    results = search_books(args.title, args.api)