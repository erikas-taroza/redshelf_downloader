import requests
import os
import re
import pdfkit
import pymupdf
import threading
from requests.adapters import HTTPAdapter, Retry
from pathlib import Path

NUM_THREADS = 1
PAGE_PATH = "pages"
COOKIES = {
    "AMP_d698e26b82": "",
    "AMP_MKTG_d698e26b82": "",
    "csrftoken": "",
    "session_id": ""
}
NUM_PAGES = 1
BOOK_URL = "https://platform.virdocs.com/spine/XXXXXXX/{}"

if not os.path.exists(PAGE_PATH):
    os.mkdir(PAGE_PATH)

CSS_REGEX = "<link.*?href=\"(.*?)\""
IMG_REGEX = "<img.*?src=\"(.*?)\""

def create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1)
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def get_raw_html(page: int) -> str:
    session = create_session()
    response = session.get(BOOK_URL.format(page), allow_redirects=True, cookies=COOKIES)
    return response.text


def get_base_url(raw: str) -> str:
    return re.search("<base href=\"(.*?/(OPS|OEBPS)).*\"/>", raw).group(1)


def get_remote_urls(raw: str) -> list[str]:
    css = re.finditer(CSS_REGEX, raw)
    imgs = re.finditer(IMG_REGEX, raw)

    remote = []

    # The format for the remote url is as follows:
    # /path/to/resource
    # The src/href that the regex picks up can come in different formats. For example:
    # 1. ../path/to/resource
    # 2. path/to/resource
    for css in css:
        parsed = css.group(1).replace("..", "")
        if parsed[0] != "/":
            parsed = f"/{parsed}"

        remote.append(parsed)

    for img in imgs:
        parsed = img.group(1).replace("..", "")
        if parsed[0] != "/":
            parsed = f"/{parsed}"

        remote.append(parsed)

    return remote


def download_remote_resources(page: int, base_url: str, urls: list[str]):
    session = create_session()
    path = f"{PAGE_PATH}/{page}"

    for url in urls:
        request_url = url
        # Static is a universal file not dependent on the book.
        if "/static" in url:
            request_url = f"https://platform.virdocs.com{url}"
        else:
            request_url = f"{base_url}{url}"

        response = session.get(request_url, allow_redirects=True, cookies=COOKIES)
        file = Path(f"{path}{url}")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(response.content)


def create_html_file(page: int, raw: str):
    # The format for the path to the file is as follows:
    # ../path/to/resource
    # The page can have different formats for a file. For example:
    # 1. /path/to/resource
    # 2. path/to/resource
    def parse_downloaded_file(match: re.Match[str]) -> str:
        parsed = match.group(1)

        if parsed[0] != "/" and ".." not in parsed:
            parsed = f"/{parsed}"

        if ".." not in parsed:
            parsed = f"..{parsed}"

        return match.group(0).replace(match.group(1), parsed)

    file = Path(f"{PAGE_PATH}/{page}/html/{page}.html")
    file.parent.mkdir(parents=True, exist_ok=True)
    parsed_raw = re.sub("<base .*?/>", "", raw)
    parsed_raw = re.sub("<script.*?>", "", parsed_raw)
    parsed_raw = re.sub(CSS_REGEX, parse_downloaded_file, parsed_raw)
    parsed_raw = re.sub(IMG_REGEX, parse_downloaded_file, parsed_raw)
    file.write_text(parsed_raw, encoding="utf-8")


def download_page(page: int):
    path = Path(f"{PAGE_PATH}/{page}")

    if not os.path.exists(path):
        os.mkdir(path)

    raw = get_raw_html(page)
    base_url = get_base_url(raw)
    remote_urls = get_remote_urls(raw)
    download_remote_resources(page, base_url, remote_urls)
    create_html_file(page, raw)


def convert_html_to_pdf(page: int):
    html = Path(f"{PAGE_PATH}/{page}/html/{page}.html").read_text(encoding="utf-8")

    def make_path(property: str, file_path: str) -> str:
        path = os.path.abspath(Path(f"{PAGE_PATH}/{page}/{file_path}"))
        return f"{property}=\"{path}\""

    # Make hrefs absolute
    html = re.sub("href=\"([.]{2})(.*?)\"", lambda match : make_path("href", match.group(2)), html)
    # Make srcs absolute
    html = re.sub("src=\"([.]{2})(.*?)\"", lambda match : make_path("src", match.group(2)), html)

    pdfkit.from_string(html, str(Path(f"{PAGE_PATH}/{page}/{page}.pdf")), options={"enable-local-file-access": ""})


def merge_pdf_files():
    main_pdf = pymupdf.open(Path(f"{PAGE_PATH}/1/1.pdf"))

    for i in range(2, NUM_PAGES + 1):
        main_pdf.insert_pdf(pymupdf.open(Path(f"{PAGE_PATH}/{i}/{i}.pdf")))

    main_pdf.save("result.pdf")


def download_thread(start: int, end: int):
    for i in range(start, end):
        print(f"[{threading.current_thread().name}] Downloading page {i}")
        download_page(i)


def convert_thread(start: int, end: int):
    for i in range(start, end):
        print(f"[{threading.current_thread().name}] Converting page {i} to PDF")
        convert_html_to_pdf(i)


assert(NUM_PAGES % NUM_THREADS == 0)
chunk_size = int(NUM_PAGES / NUM_THREADS)

# Download threads
threads: list[threading.Thread] = []
start = 1
for i in range(0, NUM_THREADS):
    thread = threading.Thread(target=download_thread, args=(start, start + chunk_size))
    thread.start()
    start += chunk_size
    threads.append(thread)

for thread in threads:
    thread.join()

# Convert threads
threads = []
start = 1
for i in range(0, NUM_THREADS):
    thread = threading.Thread(target=convert_thread, args=(start, start + chunk_size))
    thread.start()
    start += chunk_size
    threads.append(thread)

for thread in threads:
    thread.join()

print("Merging PDF files")
merge_pdf_files()
print("Complete!")
