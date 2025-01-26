import base64
import re
import requests
import os
import threading
from pathlib import Path
from requests.adapters import HTTPAdapter, Retry


class Download:
    page: int
    url: str
    raw: str

    def __init__(self, book_id: str, page: int):
        self.page = page
        self.url = "https://platform.virdocs.com/spine/{}/{}".format(book_id, self.page)

    def download(self, download_path: str, cookies: dict[str, str]):
        path = Path(f"{download_path}/{self.page}")
        if path.exists() and (path / f"html/{self.page}.html").exists():
            print(
                f"[{threading.current_thread().name}] Page {self.page} already downloaded. Skipping."
            )
            return
        if not os.path.exists(path):
            os.mkdir(path)
        self.raw = self.__get_raw_html(cookies)
        base_url = self.__get_base_url()
        remote_urls = self.__get_remote_urls()
        self.__download_remote_resources(download_path, base_url, remote_urls, cookies)
        self.__create_html_file(download_path)

    def __get_raw_html(self, cookies: dict[str, str]) -> str:
        session = self.__create_session()
        response = session.get(self.url, allow_redirects=True, cookies=cookies)
        return response.text

    def __get_base_url(self) -> str:
        return re.search('<base href="(.*?/(OPS|OEBPS)).*"/>', self.raw).group(1)

    def __get_remote_urls(self) -> list[str]:
        css = re.finditer('<link.*?href="(.*?)"', self.raw)
        imgs = re.finditer('<img.*?src="(.*?)"', self.raw)

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

    def __download_remote_resources(
        self,
        download_path: str,
        base_url: str,
        urls: list[str],
        cookies: dict[str, str],
    ):
        session = self.__create_session()
        path = f"{download_path}/{self.page}"
        for url in urls:
            request_url = url
            if "/static" in url:
                request_url = f"https://platform.virdocs.com{url}"
            else:
                request_url = f"{base_url}{url}"

            response = session.get(request_url, allow_redirects=True, cookies=cookies)
            file = Path(f"{path}{url}")
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(response.content)

    def __create_html_file(self, download_path: str):
        file = Path(f"{download_path}/{self.page}/html/{self.page}.html")
        file.parent.mkdir(parents=True, exist_ok=True)
        parsed_raw = re.sub("<base .*?/>", "", self.raw)
        parsed_raw = re.sub("<script.*?>.*?</script>", "", parsed_raw, flags=re.DOTALL)
        parsed_raw = self.__embed_images_as_base64(download_path, parsed_raw)
        file.write_text(parsed_raw, encoding="utf-8")

    def __create_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1)
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def __embed_images_as_base64(self, download_path: str, html: str) -> str:
        def encode_image(match: re.Match[str]) -> str:
            # Extract the relative path from the src attribute
            relative_path = match.group(1).replace("../", "")
            absolute_path = os.path.join(
                download_path, str(self.page), relative_path
            )  # Construct the absolute path

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
