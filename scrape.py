import requests
import os
import re
import pdfkit
import pymupdf
import threading
from requests.adapters import HTTPAdapter, Retry
from pathlib import Path

NUM_THREADS = 8
PAGE_PATH = "pages"
COOKIES = {
    "AMP_d698e26b82": "==",
    "AMP_MKTG_d698e26b82": "=",
    "csrftoken": "",
    "session_id": ""
}
NUM_PAGES = 2784
BOOK_URL = "https://platform.virdocs.com/spine/XXXXXXX/{}"

if not os.path.exists(PAGE_PATH):
    os.mkdir(PAGE_PATH)


def create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1)
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def get_raw_html(page: int) -> str:
    session = create_session()

    response = session.get(BOOK_URL.format(page), allow_redirects=True, cookies=COOKIES)
    raw_url = response.history[0].headers.get("Location")
    response = session.get(raw_url, cookies=COOKIES)
    return response.text


def get_base_url(raw: str) -> str:
    return re.search("<base href=\"(.*?/OPS).*\"/>", raw).group(1)


def get_remote_urls(raw: str) -> list[str]:
    hrefs = re.finditer("href=\"..(/.*?)\"", raw)
    srcs = re.finditer("src=\"..(/.*?)\"", raw)

    remote = []

    for href in hrefs:
        remote.append(href.group(1))

    for src in srcs:
        remote.append(src.group(1))

    return remote


def download_remote_resources(page: int, base_url: str, urls: list[str]):
    session = create_session()
    path = f"{PAGE_PATH}/{page}"

    for url in urls:
        response = session.get(f"{base_url}{url}", cookies=COOKIES)
        
        file = Path(f"{path}{url}")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(response.content)


def create_html_file(page: int, raw: str):
    file = Path(f"{PAGE_PATH}/{page}/html/{page}.html")
    file.parent.mkdir(parents=True, exist_ok=True)
    parsed_raw = re.sub("<base .*/>", "", raw)
    file.write_text(parsed_raw, encoding="utf-8")


def download_page(page: int):
    if not os.path.exists(f"{PAGE_PATH}/{page}"):
        os.mkdir(f"{PAGE_PATH}/{page}")

    raw = get_raw_html(page)
    base_url = get_base_url(raw)
    remote_urls = get_remote_urls(raw)
    download_remote_resources(page, base_url, remote_urls)
    create_html_file(page, raw)


def convert_html_to_pdf(page: int):
    file = open(f"{PAGE_PATH}/{page}/html/{page}.html", "r")
    html = file.read()

    # Make hrefs absolute
    html = re.sub("href=\"([.]{2})", f"href=\"{os.path.abspath(f"{PAGE_PATH}/{page}")}", html)
    # Make srcs absolute
    html = re.sub("src=\"([.]{2})", f"src=\"{os.path.abspath(f"{PAGE_PATH}/{page}")}", html)

    pdfkit.from_string(html, f"{PAGE_PATH}/{page}/{page}.pdf", options={"enable-local-file-access": ""})
    file.close()



def merge_pdf_files():
    main_pdf = pymupdf.open(f"{PAGE_PATH}/1/1.pdf")

    for i in range(2, NUM_PAGES + 1):
        main_pdf.insert_pdf(pymupdf.open(f"{PAGE_PATH}/{i}/{i}.pdf"))

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
