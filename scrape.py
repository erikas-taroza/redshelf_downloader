import os
import pymupdf
import threading
from pathlib import Path
from redshelf_downloader.download import Download
from redshelf_downloader.convert_to_pdf import ConvertToPdf

NUM_THREADS = 1
PAGE_PATH = "pages"
COOKIES = {
    "AMP_d698e26b82": "",
    "AMP_MKTG_d698e26b82": "",
    "csrftoken": "",
    "session_id": "",
}
NUM_PAGES = 1
BOOK_ID = "XXXXXXX"


def merge_pdf_files():
    main_pdf = pymupdf.open(Path(f"{PAGE_PATH}/1/1.pdf"))
    for i in range(2, NUM_PAGES + 1):
        main_pdf.insert_pdf(pymupdf.open(Path(f"{PAGE_PATH}/{i}/{i}.pdf")))
    main_pdf.save("result.pdf")


def download_thread(start: int, end: int):
    for i in range(start, end):
        print(f"[{threading.current_thread().name}] Downloading page {i}")
        Download(BOOK_ID, i).download(PAGE_PATH, COOKIES)


def convert_thread(start: int, end: int):
    for i in range(start, end):
        print(f"[{threading.current_thread().name}] Converting page {i} to PDF")
        ConvertToPdf(PAGE_PATH, i).convert()


if __name__ == "__main__":
    if not os.path.exists(PAGE_PATH):
        os.mkdir(PAGE_PATH)

    assert NUM_PAGES % NUM_THREADS == 0
    chunk_size = int(NUM_PAGES / NUM_THREADS)

    threads = []
    start = 8
    for i in range(0, NUM_THREADS):
        thread = threading.Thread(
            target=download_thread, args=(start, start + chunk_size)
        )
        thread.start()
        start += chunk_size
        threads.append(thread)

    for thread in threads:
        thread.join()

    threads = []
    start = 1
    for i in range(0, NUM_THREADS):
        thread = threading.Thread(
            target=convert_thread, args=(start, start + chunk_size)
        )
        thread.start()
        start += chunk_size
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("Merging PDF files")
    merge_pdf_files()
    print("Complete!")
