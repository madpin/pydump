"""
**Core Functionality:**

1.  **URL Scanning:**
    *   Takes a website URL and a file extension (like ".pdf", ".zip", ".mp3") as input.
    *   Crawls the webpage, looking for links that end with the specified file extension.
    *   It uses `requests` to fetch the page and `BeautifulSoup` to parse the HTML.
    *   It's smart enough to handle relative URLs, converting them to absolute ones.
    *   It uses `lxml` parser for better performance when parsing the HTML.
2.  **File Downloading:**
    *   Once it finds matching files, it downloads them to a local directory.
    *   It streams the download in chunks to handle large files efficiently.
    *   It shows a progress bar using `streamlit` to let you know how the download is going.
    *   It also checks if the file size exceeds a limit (100MB by default).
    *   It has a retry mechanism in case the download fails.
    *   It sanitizes filenames to avoid issues.
3.  **User Interface (Streamlit):**
    *   It creates a simple web app where you can enter a URL and choose a file type.
    *   It displays the list of found files with download buttons.
    *   It has a "Download All" button for convenience.
    *   It shows error messages if something goes wrong (like an invalid URL or download failure).

**Key Components:**

*   **`FileInfo` Data Class:**  Holds information about each file (URL, filename, extension, size). It also validates the URL and filename.
*   **`URLScanner` Class:**  Handles the scanning of URLs, finding file links based on the extension.
*   **`FileDownloader` Class:**  Manages the download process, including retries, progress tracking, and file size verification.
*   **`StreamlitUI` Class:**  Sets up the Streamlit UI, manages the application flow, and handles user interactions.

**Tech Stack:**

*   **Python:** The main language.
*   **Streamlit:** For the web UI.
*   **Requests:** For making HTTP requests.
*   **BeautifulSoup:** For parsing HTML.
*   **validators:** For URL validation.
*   **dataclasses:** For creating the `FileInfo` class.
*   **pathlib:** For handling file paths in a more object-oriented way.

**How it works:**

1.  The `main()` function initializes the `StreamlitUI` class.
2.  The `setup_page()` method sets the Streamlit page configurations.
3.  The `render_ui()` method displays the input fields (URL and file type) and the "Scan for Files" button.
4.  When you click "Scan for Files," it uses the `URLScanner` to find the file links.
5.  The results are stored in the Streamlit session state, so they persist between interactions.
6.  The `show_results()` method displays the list of files and their download buttons.
7.  When you click the "Download" button, it uses the `FileDownloader` to download the file, showing a progress bar.
8.  The `download_all_files()` method downloads all files found with an overall progress bar.

**In Thiago's words:**

Basically, this script is a handy tool for grabbing specific types of files from any website.
You punch in the URL, pick the file type, and boom, it goes to work,
downloading all the files it finds. It's like having a personal download manager built in Python.

Let me know if you have any more questions, or if you want to dive into any specific part of the code.
"""

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
import validators

# Configuration and Constants
ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "txt",
    "csv",
    "xls",
    "xlsx",
    "zip",
    "rar",
    "mp3",
    "mp4",
    "jpg",
    "jpeg",
    "png",
    "gif",
}
CHUNK_SIZE = 8192
MAX_RETRIES = 3

# Environment variables with defaults
DOWNLOAD_PATH = Path(os.getenv("DOWNLOAD_PATH", "./downloads"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 100_000_000))  # 100MB
TIMEOUT = int(os.getenv("TIMEOUT", 30))  # seconds


@dataclass
class FileInfo:
    """Data class to store file information with validation"""

    url: str
    filename: str
    extension: str
    size: Optional[int] = None

    def __post_init__(self):
        """Validate fields after initialization"""
        if not self.url or not self.filename:
            raise ValueError("URL and filename must not be empty")
        if self.extension and not self.extension.startswith("."):
            self.extension = f".{self.extension}"


class URLScanner:
    """Handles URL scanning and file detection with optimized performance"""

    def __init__(self, base_url: str, file_extension: str):
        """Initialize scanner with validation"""
        self.base_url = base_url.strip()
        self.file_extension = file_extension.lower()
        if not self.file_extension.startswith("."):
            self.file_extension = f".{self.file_extension}"

        # Setup session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; FileDownloader/1.0)"}
        )

    def validate_url(self) -> bool:
        """Validate URL format and accessibility"""
        try:
            return bool(validators.url(self.base_url))
        except validators.ValidationFailure:
            return False

    def get_file_links(self) -> Set[str]:
        """Scan URL for files with optimized parsing"""
        if not self.validate_url():
            raise ValueError("Invalid URL format")

        file_urls = set()
        try:
            response = self.session.get(
                self.base_url, timeout=TIMEOUT, allow_redirects=True
            )
            response.raise_for_status()

            # Use lxml parser for better performance
            soup = BeautifulSoup(response.content, "lxml")

            # Optimize link extraction with CSS selector
            for link in soup.select("a[href]"):
                href = link.get("href", "").strip()
                if href and href.lower().endswith(self.file_extension):
                    absolute_url = self.normalize_url(href)
                    if absolute_url:
                        file_urls.add(absolute_url)

        except requests.RequestException as e:
            st.error(f"Error scanning URL: {str(e)}")
            return set()

        return file_urls

    def normalize_url(self, url: str) -> str:
        """Convert URLs to absolute with validation"""
        try:
            # Handle already absolute URLs
            if bool(urlparse(url).netloc):
                return url
            # Convert relative to absolute
            return urljoin(self.base_url, url)
        except Exception:
            return ""


class FileDownloader:
    """Handles file downloading with safety checks and progress tracking"""

    def __init__(self, download_path: Path):
        """Initialize downloader with path creation"""
        self.download_path = download_path
        self.download_path.mkdir(parents=True, exist_ok=True)

        # Setup session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; FileDownloader/1.0)"}
        )

    def download_file(self, file_info: FileInfo) -> Tuple[bool, str]:
        """Download file with retry mechanism and progress tracking"""
        if not self.verify_file_size(file_info.url):
            return False, "File size exceeds limit"

        safe_filename = self._sanitize_filename(file_info.filename)
        file_path = self.download_path / safe_filename

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(file_info.url, stream=True, timeout=TIMEOUT)
                response.raise_for_status()

                # Verify content type
                content_type = response.headers.get("content-type", "")
                if "html" in content_type.lower():
                    return False, "Invalid content type"

                # Stream download with progress
                total_size = int(response.headers.get("content-length", 0))
                progress_bar = st.progress(0)

                with open(file_path, "wb") as f:
                    downloaded_size = 0
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size:
                                progress = min(downloaded_size / total_size, 1.0)
                                progress_bar.progress(progress)

                return True, f"Successfully downloaded to {safe_filename}"

            except requests.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    return (
                        False,
                        f"Download failed after {MAX_RETRIES} attempts: {str(e)}",
                    )
                time.sleep(1)  # Brief delay before retry

    def verify_file_size(self, url: str) -> bool:
        """Check file size with HEAD request"""
        try:
            response = self.session.head(url, timeout=TIMEOUT)
            size = int(response.headers.get("content-length", 0))
            return size <= MAX_FILE_SIZE
        except (requests.RequestException, ValueError):
            return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove potentially dangerous characters
        safe_filename = re.sub(r"[^\w\-_. ]", "", filename)
        # Ensure filename isn't empty
        return safe_filename or "download"


class StreamlitUI:
    """Manages Streamlit interface and application flow"""

    def __init__(self):
        """Initialize UI components and state"""
        self.downloader = FileDownloader(DOWNLOAD_PATH)
        # Initialize session state if not already done
        if "files" not in st.session_state:
            st.session_state.files = []

    def setup_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(page_title="File Downloader", page_icon="📥", layout="wide")
        st.title("Web File Downloader")
        st.markdown("""
        Download files of specific types from any website.
        Enter a URL and select the file type you want to download.
        """)

    def render_ui(self):
        """Render main application interface"""
        # Input section
        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input("Enter Website URL:", placeholder="https://example.com")
        with col2:
            extension = st.selectbox("File Type:", list(ALLOWED_EXTENSIONS))

        if st.button("Scan for Files"):
            if not url:
                st.error("Please enter a URL")
                return

            try:
                scanner = URLScanner(url, extension)
                with st.spinner("Scanning for files..."):
                    file_urls = scanner.get_file_links()

                if not file_urls:
                    st.warning(f"No {extension} files found at the given URL")
                    return

                # Store files in session state
                st.session_state.files = [
                    FileInfo(
                        url=file_url,
                        filename=os.path.basename(urlparse(file_url).path),
                        extension=extension,
                    )
                    for file_url in file_urls
                ]

            except Exception as e:
                st.error(f"Error: {str(e)}")

        # Show results if files exist in session state
        if st.session_state.files:
            self.show_results(st.session_state.files)

    def show_results(self, files: List[FileInfo]):
        """Display found files and download options"""
        st.subheader("Found Files")

        # Display file count
        st.write(f"Found {len(files)} files")

        # Add Download All button at the top
        if st.button("Download All Files", key="download_all"):
            self.download_all_files(files)

        # Individual file listings
        for idx, file in enumerate(files):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(file.filename)
            with col2:
                if st.button("Download", key=f"download_{idx}"):
                    self.show_download_progress(file)

    def show_download_progress(self, file: FileInfo):
        """Handle file download and progress display"""
        with st.spinner(f"Downloading {file.filename}..."):
            success, message = self.downloader.download_file(file)

        if success:
            st.success(message)
        else:
            st.error(message)

    def download_all_files(self, files: List[FileInfo]):
        """Download all files with progress tracking"""
        success_count = 0
        total_files = len(files)

        # Create overall progress bar
        overall_progress = st.progress(0)
        status_text = st.empty()

        for idx, file in enumerate(files, 1):
            status_text.text(f"Downloading {file.filename} ({idx}/{total_files})")

            with st.spinner(f"Downloading {file.filename}..."):
                success, message = self.downloader.download_file(file)

                if success:
                    success_count += 1
                    st.success(f"✅ {file.filename}: {message}")
                else:
                    st.error(f"❌ {file.filename}: {message}")

            # Update overall progress
            overall_progress.progress(idx / total_files)

        # Show final summary
        if success_count == total_files:
            st.success(f"Successfully downloaded all {total_files} files!")
        else:
            st.warning(f"Downloaded {success_count} out of {total_files} files")


def main():
    """Main application entry point"""
    # Initialize application
    app = StreamlitUI()

    # Setup page
    app.setup_page()

    # Render main UI
    app.render_ui()


if __name__ == "__main__":
    main()
