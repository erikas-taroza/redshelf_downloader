import json
import os
import sys


class Config:
    num_threads: int
    num_pages: int
    download_path: str
    book_id: str
    cookies: dict[str, str]

    def __init__(self):
        if not os.path.exists("config.json"):
            with open("config.json", "w") as config:
                config.write("""{
    "num_threads": 1,
    "num_pages": 1,
    "download_path": "pages",
    "book_id": "XXXXXXX",
    "cookies": {
        "AMP_d698e26b82": "",
        "AMP_MKTG_d698e26b82": "",
        "csrftoken": "",
        "session_id": ""
    }
}""")

        config_file = open("config.json", "r")
        config = json.loads(config_file.read())

        self.num_threads = config["num_threads"]
        self.num_pages = config["num_pages"]
        self.download_path = config["download_path"]
        self.book_id = config["book_id"]
        self.cookies = config["cookies"]

    def validate(self):
        if (
            self.book_id == "XXXXXXX"
            or len(self.book_id) == 0
            or len(self.cookies) == 0
            or len(list(self.cookies.values())[0]) == 0
        ):
            print(
                "Invalid config. Please double check that the values in `config.json` are correct."
            )
            sys.exit(1)
