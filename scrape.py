import os
import pymupdf
import threading
from pathlib import Path
from redshelf_downloader.download import Download
from redshelf_downloader.convert_to_pdf import ConvertToPdf
from redshelf_downloader.config import Config


def merge_pdf_files(download_path: str, num_pages: int):
    main_pdf = pymupdf.open(Path(f"{download_path}/1/1.pdf"))
    for i in range(2, num_pages + 1):
        main_pdf.insert_pdf(pymupdf.open(Path(f"{download_path}/{i}/{i}.pdf")))
    main_pdf.save("result.pdf")


def download_thread(start: int, end: int, config: Config):
    for i in range(start, end):
        print(f"[{threading.current_thread().name}] Downloading page {i}")
        Download(config.book_id, i).download(config.download_path, config.cookies)


def convert_thread(start: int, end: int, config: Config):
    for i in range(start, end):
        print(f"[{threading.current_thread().name}] Converting page {i} to PDF")
        ConvertToPdf(config.download_path, i).convert()


if __name__ == "__main__":
    config = Config()
    config.validate()

    if not os.path.exists(config.download_path):
        os.mkdir(config.download_path)

    assert config.num_pages % config.num_threads == 0
    chunk_size = int(config.num_pages / config.num_threads)

    threads = []
    start = 1
    for i in range(0, config.num_threads):
        thread = threading.Thread(
            target=download_thread, args=(start, start + chunk_size, config)
        )
        thread.start()
        start += chunk_size
        threads.append(thread)

    for thread in threads:
        thread.join()

    threads = []
    start = 1
    for i in range(0, config.num_threads):
        thread = threading.Thread(
            target=convert_thread, args=(start, start + chunk_size, config)
        )
        thread.start()
        start += chunk_size
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("Merging PDF files")
    merge_pdf_files(config.download_path, config.num_pages)
    print("Complete!")
