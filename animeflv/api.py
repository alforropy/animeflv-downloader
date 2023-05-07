import requests
import os
import bs4
import re
from tqdm import tqdm
from pathlib import Path
import time
import json
from selenium.webdriver import Chrome, Firefox, FirefoxOptions, FirefoxProfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
profile = FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.dir", "./")
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

def search_anime(query: str, find_details:bool = True):
    print(f"Searching query: {query}")
    url = f"https://www3.animeflv.net/browse?q={query}"
    html = requests.get(url).text
    soup = bs4.BeautifulSoup(html, features="html.parser")

    items = soup.find("ul", {'class': 'ListAnimes'}).find_all('li')
    results = {}

    for item in tqdm(items, desc="Looking up details", unit=' title'):
        title = item.find("h3", {'class': 'Title'}).text
        item_url = item.find('a').attrs['href'].replace('/anime/', "")

        if find_details:
            item_html = requests.get(f"https://www3.animeflv.net/anime/{item_url}").text
            anime_details = re.search(r"var episodes = (?P<list_items>\[.+\]);", item_html).groups('list_items')[0]
            total_chapters = eval(anime_details)[0][0]
        else:
            total_chapters = None

        results[title] = (item_url, total_chapters)

    return results


def find_details(anime_id:str):
    item_html = requests.get(f"https://www3.animeflv.net/anime/{anime_id}").text
    anime_details = re.search(r"var episodes = (?P<list_items>\[.+\]);", item_html).groups('list_items')[0]
    description = bs4.BeautifulSoup(item_html, features="html.parser").find("div", {'class': 'Description'}).text
    total_chapters = eval(anime_details)[0][0]

    return total_chapters, description


def download_one(title: str, chapter: int, output_path: str, return_url:bool=False, override:bool = False):
    print(f"Downloading {title}-{chapter}")
    current_dir = os.getcwd()
    path = Path(output_path) / f"{title}-{chapter}.mp4"

    if path.exists():
        if not override:
            print("(!) Refusing to override. Pass override=True (--override in the CLI) to force.")
            return

    print("Downloading AnimeFLV.net webpage")
    dr = Firefox()
    dr.get(f"https://www3.animeflv.net/ver/{title}-{chapter}")
    bs = bs4.BeautifulSoup(dr.page_source,"lxml")
    html = dr.page_source
    print("Looking for GoCDN link")

    soup = bs4.BeautifulSoup(html, features="html.parser")
    lines = str(soup).split("\n")
    for l in lines:
        if l.strip().startswith("var videos = {"):
            break

    l = l.strip()
    dr.close()
    data = json.loads(l[13:-1])

    for d in data["SUB"]:
        print(d)
        if d["server"] == "yu":
            break


    url = d["code"]

    print("Found GoCDN url")
    print(url)

    print("Opening Firefox (for later...)")

    profile.set_preference("browser.download.dir", current_dir+'/'+ title)
    driver = Firefox(firefox_profile=profile)
    print("Getting the URL")

    url = url.replace("embed","watch")
    driver.get(url)

    print("Clicking the play button")
    play = driver.find_element_by_link_text("Download")
    driver.execute_script("arguments[0].click();", play)


    time.sleep(5)

    play = driver.find_element_by_link_text("Download")
    driver.execute_script("arguments[0].click();", play)    
    time.sleep(300)
    driver.close()
    return path    
'''
    if path.exists():
        print(f"(!) Overwriting {path}")

    try:
        with path.open("wb") as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                for data in stream.iter_content(32*1024):
                    f.write(data)
                    pbar.update(len(data))
    except:
        path.unlink()
        raise

    return path
'''
