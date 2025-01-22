import requests
import os
import re
import pdfkit
import pymupdf
import threading
import base64
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
        if "/static" in url:
            request_url = f"https://platform.virdocs.com{url}"
        else:
            request_url = f"{base_url}{url}"

        response = session.get(request_url, allow_redirects=True, cookies=COOKIES)
        file = Path(f"{path}{url}")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(response.content)

def embed_images_as_base64(html: str, page: int) -> str:
    def encode_image(match: re.Match[str]) -> str:
        # Extract the relative path from the src attribute
        relative_path = match.group(1).replace("../", "")
        absolute_path = os.path.join(PAGE_PATH, str(page), relative_path)  # Construct the absolute path

        try:
            # Read the image file and encode it as base64
            with open(absolute_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            return f'src="data:image/png;base64,{encoded}"'
        except FileNotFoundError:
            print(f"Image not found: {absolute_path}")
            return match.group(0)  # Keep the original src if the image is not found

    # Replace all src attributes with base64-encoded images
    return re.sub(r'src="(.*?)"', encode_image, html)



def create_html_file(page: int, raw: str):
    file = Path(f"{PAGE_PATH}/{page}/html/{page}.html")
    file.parent.mkdir(parents=True, exist_ok=True)
    parsed_raw = re.sub("<base .*?/>", "", raw)
    parsed_raw = re.sub("<script.*?>.*?</script>", "", parsed_raw, flags=re.DOTALL)
    parsed_raw = embed_images_as_base64(parsed_raw, page)
    file.write_text(parsed_raw, encoding="utf-8")

def download_page(page: int):
    path = Path(f"{PAGE_PATH}/{page}")
    if path.exists() and (path / f"html/{page}.html").exists():
        print(f"[{threading.current_thread().name}] Page {page} already downloaded. Skipping.")
        return
    if not os.path.exists(path):
        os.mkdir(path)
    raw = get_raw_html(page)
    base_url = get_base_url(raw)
    remote_urls = get_remote_urls(raw)
    download_remote_resources(page, base_url, remote_urls)
    create_html_file(page, raw)

def convert_html_to_pdf(page: int):
    html_path = Path(f"{PAGE_PATH}/{page}/html/{page}.html")
    pdf_path = Path(f"{PAGE_PATH}/{page}/{page}.pdf")
    try:
        pdfkit.from_file(
            str(html_path),
            str(pdf_path),
            options={"enable-local-file-access": ""}
        )
    except Exception as e:
        print(f"Failed to convert page {page} to PDF: {e}")

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

threads = []
start = 1
for i in range(0, NUM_THREADS):
    thread = threading.Thread(target=download_thread, args=(start, start + chunk_size))
    thread.start()
    start += chunk_size
    threads.append(thread)

for thread in threads:
    thread.join()

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
