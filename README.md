# RedShelf Downloader

Downloads the content of each page of the textbook and converts it to a PDF file.

Each page is stored in an independent folder so if you want to compile the textbook in a different way, you can.

## Dependencies

- requests
- pdfkit
- pymupdf
- wkhtmltopdf (not from pip)

```sh
pip install requests pdfkit pymupdf
```

Install `wkhtmltopdf` using your package manager or from [their website](https://wkhtmltopdf.org/downloads.html). Make sure that it is added to your PATH environment variable as well.

## Configure

```py
NUM_THREADS = 8
PAGE_PATH = "pages"
COOKIES = {
    "AMP_d698e26b82": "==",
    "AMP_MKTG_d698e26b82": "=",
    "csrftoken": "",
    "session_id": ""
}
NUM_PAGES = 0
BOOK_URL = "https://platform.virdocs.com/spine/XXXXXXX/{}"
```

To get the values for `COOKIES`, `NUM_PAGES`, and `BOOK_URL`, open the textbook in the browser.

### COOKIES

Enter the browser's devtools and inspect a network request for the page (in the file column, it should be a single number). Click on the request and copy and paste the cookies into the file.

### NUM_PAGES / BOOK_URL

Go all the way to the end of the textbook and look at the url.

The url should be formatted like so:
https://platform.virdocs.com/read/book_id/page_number

In `BOOK_URL` replace the X's with the book ID. Update `NUM_PAGES` with the page number in the URL, not in the UI of the website.

### NUM_THREADS

The number of threads to use to download the book. The higher the number, the faster the book will download. Make sure that the number specificed can evenly divided `NUM_PAGES`. For example, if you have 10 pages, `NUM_THREADS` can be 1, 2, 5, or 10. It cannot be 4 because 10/4 is not a whole number.

## Usage

```sh
python scrape.py
```
