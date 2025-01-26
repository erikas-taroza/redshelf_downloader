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

## Usage

```sh
python scrape.py
```

## Configure

Before using this tool, you must configure the `config.json` file. If file is not present, run the program to automatically generate it.

It should look something like this:

```json
{
  "num_threads": 1,
  "num_pages": 1,
  "download_path": "pages",
  "book_id": "",
  "cookies": {
    "csrftoken": "",
    "session_id": ""
  }
}
```

To get the values for `cookies`, `num_pages`, and `book_id`, open the textbook in the browser.

### Cookies

Enter the browser's devtools and inspect a network request for the page (in the file column, it should be a single number). Click on the request and copy and paste the cookies into the file.

### Num Pages / Book ID

Go all the way to the end of the textbook and look at the url.

The url should be formatted like so:
https://platform.virdocs.com/read/book_id/page_number

In `book_id` replace the X's with the book ID in the url. Update `num_pages` with the page number in the URL, not in the UI of the website.

### Num Threads

The number of threads to use to download the book. The higher the number, the faster the book will download but you may run into rate limits at higher numbers.
