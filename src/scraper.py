"""
Dinosaur Comics (Qwantz) Comic Scraper

This module provides functionality to scrape Dinosaur Comics from qwantz.com,
including the comic image and title information. It fetches the current
latest comic from the Dinosaur Comics website.

Usage:
    python scraper.py
"""

import datetime
import os
from typing import Optional, Dict
from bs4 import BeautifulSoup
import requests


# Constants
QWANTZ_BASE_URL = 'https://www.qwantz.com/'
INVALID_FILENAME_CHARS = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.']


def sanitize_filename(filename: str) -> str:
    """
    Remove characters from a string that are invalid in filenames.

    Args:
        filename: The original filename string to sanitize

    Returns:
        A sanitized filename string with invalid characters removed
    """
    return ''.join(char for char in filename if char not in INVALID_FILENAME_CHARS)


def fetch_webpage(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch and parse a webpage into a BeautifulSoup object.

    Args:
        url: The URL of the webpage to fetch

    Returns:
        BeautifulSoup object if successful, None if request fails
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_comic_data(soup: BeautifulSoup) -> Optional[Dict[str, str]]:
    """
    Extract comic data (image URL, title) from parsed HTML.

    Args:
        soup: BeautifulSoup object containing the parsed Qwantz page

    Returns:
        Dictionary containing 'image_url' and 'title' keys,
        or None if extraction fails
    """
    try:
        # Find the comic image
        comic_img = soup.find('img', class_='comic')
        if not comic_img:
            print("Error: Could not find comic image")
            return None

        # Extract image URL (relative path)
        image_src = comic_img.get('src')
        if not image_src:
            print("Error: Could not extract image source")
            return None

        # Construct full URL
        image_url = QWANTZ_BASE_URL + image_src

        # Extract title from the image title attribute
        title = comic_img.get('title', 'unknown')

        return {
            'image_url': image_url,
            'title': title
        }
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error extracting comic data: {e}")
        return None


def download_image(image_url: str) -> Optional[bytes]:
    """
    Download image data from a URL.

    Args:
        image_url: The URL of the image to download

    Returns:
        Image data as bytes if successful, None if download fails
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None


def save_image(image_data: bytes, filepath: str) -> bool:
    """
    Save image data to a file.

    Args:
        image_data: The image data as bytes
        filepath: The path where the image should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'wb') as handler:
            handler.write(image_data)
        return True
    except IOError as e:
        print(f"Error saving image to {filepath}: {e}")
        return False


def get_file_extension(url: str) -> str:
    """
    Extract file extension from a URL.

    Args:
        url: The URL to extract extension from

    Returns:
        File extension (e.g., 'png', 'jpg')
    """
    return url.split('.')[-1].split('?')[0]  # Handle query parameters


def get_current_comic() -> bool:
    """
    Download the current latest Dinosaur Comics comic.

    This function fetches the Dinosaur Comics homepage to get the latest comic,
    then downloads the image and saves metadata to the current working directory.

    Returns:
        True if successful, False otherwise
    """
    # Fetch the main Qwantz page
    soup = fetch_webpage(QWANTZ_BASE_URL)
    if soup is None:
        return False

    # Extract comic data
    comic_data = extract_comic_data(soup)
    if comic_data is None:
        return False

    # Create filename from image URL
    image_filename = comic_data['image_url'].split('/')[-1]
    base_filename = image_filename.rsplit('.', 1)[0]  # Remove extension

    # Download the image
    image_data = download_image(comic_data['image_url'])
    if image_data is None:
        return False

    # Save the image
    file_extension = get_file_extension(comic_data['image_url'])
    image_path = f"{base_filename}.{file_extension}"
    if not save_image(image_data, image_path):
        return False

    # Save metadata
    metadata_path = f"{base_filename}_metadata.txt"
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(f"Title: {comic_data['title']}\n")
            f.write(f"Image URL: {comic_data['image_url']}\n")
    except IOError as e:
        print(f"Error saving metadata to {metadata_path}: {e}")
        return False

    print(f"Successfully downloaded current comic: {base_filename}")
    print(f"Title: {comic_data['title']}")
    return True


def setup_daily_directory() -> str:
    """
    Create and return the path to today's data directory.

    Creates a directory structure: data/YYYY-MM-DD/ relative to the project root.

    Returns:
        The absolute path to the created directory
    """
    # Get current date
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Construct path to data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data', date)

    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    return data_dir


def main():
    """
    Main function to run the daily comic scraper.

    Sets up the daily directory and downloads the current Dinosaur Comics comic.
    """
    # Create and change to today's data directory
    data_dir = setup_daily_directory()
    os.chdir(data_dir)

    print(f"Saving comic to: {data_dir}")

    # Download the current comic
    success = get_current_comic()

    if success:
        print("Comic download completed successfully!")
    else:
        print("Failed to download comic.")


if __name__ == "__main__":
    main()

