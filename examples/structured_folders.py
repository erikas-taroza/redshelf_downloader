import os
import re
import base64

PAGE_PATH = "pages"
PATH = "textbook"
NUM_PAGES = 2784

def roman_to_int(s):
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]

    return int_val


def process_html_file(page: int, html: str) -> str:
    def insert_in_head(source: str, content: str) -> str:
        head_idx = html.index("<head>")
        return f"{source[:head_idx + 6]}{content}{source[head_idx + 6:]}"
    
    def convert_image_to_base64(image_path: str) -> str:
        extension = image_path.split(".")[1]
        with open(f"{PAGE_PATH}/{page}/{image_path}", "rb") as image:
            encoded = base64.b64encode(image.read())
            return f"data:image/{extension};base64,{encoded.decode()}"


    processed = html

    # Insert CSS
    primary_css = re.finditer("<link rel=\"stylesheet\".*?href=\"../(.*?)\"/>", processed)
    for match in primary_css:
        with open(f"{PAGE_PATH}/{page}/{match.group(1)}", "r") as css:
            processed = insert_in_head(processed, f"<style>{css.read()}</style>")

    # Convert images to base64
    processed = re.sub("<img.*?src=\"(../(.*?))\".*?/>", lambda match : match.group(0).replace(match.group(1), convert_image_to_base64(match.group(2))), processed)

    return processed


def organize() -> dict[str, list[int]]:
    # Describes which files contain the pages it used
    page_map: dict[str, list[int]] = {}

    def add_to_page_map(key: str, page: int):
        if key not in page_map.keys():
            page_map[key] = []
        page_map[key].append(page)

    reached_first_section = False
    section_name = ""
    chapter_name = ""
    chapter_content = ""

    intro_content = ""

    glossary_name = ""
    glossary_content = ""
    glossary_titles = ["Glossary", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "Contents"]

    for i in range(1, NUM_PAGES + 1):
        file = open(f"{PAGE_PATH}/{i}/html/{i}.html", "r")
        html = process_html_file(i, file.read())
        title = re.search("<title>(.*?)</title>", html).group(1).strip()

        # Content before the section
        if not reached_first_section and "Section" not in title:
            add_to_page_map("_Introduction.html", i)
            intro_content += html

        if "Glossary" in title:
            chapter_name = ""
            section_name = ""
            if not os.path.exists(f"{PATH}/Glossary"):
                os.mkdir(f"{PATH}/Glossary")

        if "Section" in title:
            title = re.sub("Section(\s.*?\s).*", lambda match : match.group(0).replace(match.group(1), f" {str(roman_to_int(match.group(1).strip()))} "), title)
            if not os.path.exists(f"{PATH}/{title}"):
                os.mkdir(f"{PATH}/{title}")
            with open(f"{PATH}/{title}/_{title}.html", "w") as file:
                file.write(html)
                add_to_page_map(f"{title}/_{title}.html", i)
            section_name = title
            chapter_content = ""
            chapter_name = ""
            reached_first_section = True
            continue


        if "Chapter" in title:
            # Reached next chapter, write previous chapter as 1 whole file.
            if len(chapter_content) != 0:
                with open(f"{PATH}/{section_name}/{chapter_name}.html", "w") as file:
                    file.write(chapter_content)
                chapter_content = ""
                chapter_name = ""
            else:
                chapter_name = title.replace("/", " ")
        
        if len(chapter_name) != 0:
            chapter_content += html
            add_to_page_map(f"{section_name}/{chapter_name}.html", i)
            continue

        # Glossary
        if title in glossary_titles or glossary_name == "Contents" and title not in glossary_titles:
            if len(glossary_content) != 0:
                with open(f"{PATH}/Glossary/{glossary_name}.html", "w") as file:
                    file.write(glossary_content)
                glossary_name = title
                glossary_content = ""
            else:
                glossary_name = title
        
        if len(glossary_name) != 0 and glossary_name in glossary_titles:
            glossary_content += html
            add_to_page_map(f"Glossary/{glossary_name}.html", i)


    with open(f"{PATH}/_Introduction.html", "w") as file:
        file.write(intro_content)

    return page_map


def fix_links(page_map: dict[str, list[int]]):
    for path in page_map.keys():
        file = open(f"{PATH}/{path}", "r")
        html = file.read()
        file.close()
        links = re.finditer("<a.*?href=\"([?]#po(.*?):(.*?))\">", html)
        
        for match in links:
            page_number = int(match.group(2)) + 1
            ref = match.group(3)
            
            for page in page_map.items():
                if page_number in page[1]:
                    html = html.replace(match.group(1), f"../{page[0]}#{ref}")

        with open(f"{PATH}/{path}", "w") as file:
            file.write(html)


if not os.path.exists(PATH):
    os.mkdir(PATH)

fix_links(organize())
