from pathlib import Path

import pdfkit


class ConvertToPdf:
    path: str
    page: int

    def __init__(self, path: str, page: int):
        self.path = path
        self.page = page

    def convert(self):
        html_path = Path(f"{self.path}/{self.page}/html/{self.page}.html")
        pdf_path = Path(f"{self.path}/{self.page}/{self.page}.pdf")
        try:
            pdfkit.from_file(
                str(html_path),
                str(pdf_path),
                options={"enable-local-file-access": "", "encoding": "UTF-8"},
            )
        except Exception as e:
            print(f"Failed to convert page {self.page} to PDF: {e}")
