from typing import List
from rich.table import Table
from ..models.book import BookInfo


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
