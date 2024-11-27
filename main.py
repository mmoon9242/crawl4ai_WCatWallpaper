import asyncio
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

import re

import os
import requests

import argparse


def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(invalid_chars, "-", filename)
    return sanitized_filename


def download_file(url, save_directory="."):
    filename = os.path.basename(url)
    save_path = os.path.join(save_directory, filename)

    # 如果資料夾不存在，則建立一個資料夾
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Download: {save_path}")
    else:
        print(f"Download error, error code: {response.status_code}")


def replace_relative_path_with_url(path, base_url="https://example.com"):
    if path.startswith("./"):
        return base_url + path[1:]
    return path

async def getWCatWallpaper(index=0):
    schemaNews = {
        "name": "WCat News",
        "baseSelector": "li.entry",
        "fields": [
            {"name": "title", "selector": "h3.entryTitle", "type": "text"},
            {"name": "time", "selector": ".date", "type": "text"},
            {
                "name": "link",
                "selector": "a[href]",
                "type": "attribute",
                "attribute": "href",
            },
            {
                "name": "thumb",
                "type": "nested",
                "selector": "img",
                "fields": [
                    {"name": "src", "type": "attribute", "attribute": "src"},
                    {"name": "alt", "type": "attribute", "attribute": "alt"},
                ],
            },
        ],
    }
    extractionStrategyNews = JsonCssExtractionStrategy(schemaNews, verbose=True)
    schemaWallpapers = {
        "name": "WCat Wallpapers",
        "baseSelector": "li.p-wallpaper__listItem, div.wpArea li",
        "fields": [
            {
                "name": "wallpaper",
                "type": "nested_list",
                "selector": "li.p-wallpaper__linksItem, div.link.shareCover p",
                "fields": [
                    {"name": "size", "selector": "a", "type": "text"},
                    {
                        "name": "image",
                        "selector": "a",
                        "attribute": "href",
                        "type": "attribute",
                    },
                ],
            }
        ],
    }
    extractionStrategyWallpapers = JsonCssExtractionStrategy(
        schemaWallpapers, verbose=True
    )

    WCatNews = None
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://colopl.co.jp/shironekoproject/news",
            extraction_strategy=extractionStrategyNews,
            bypass_cache=True,
        )
        assert result.success, "WCat News error."
        WCatNews = json.loads(result.extracted_content)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=f"https://colopl.co.jp{WCatNews[index]["link"]}",
            extraction_strategy=extractionStrategyWallpapers,
            bypass_cache=True,
        )
        assert result.success, "WCat Wallpapers error."
        WCatWallpapers = json.loads(result.extracted_content)

    print(f"Success, {len(WCatNews)} news")
    print(json.dumps(WCatNews[index], indent=2, ensure_ascii=False))
    print(json.dumps(WCatWallpapers, indent=2, ensure_ascii=False))

    for Wallpapers in WCatWallpapers:
        for wallpaper in Wallpapers["wallpaper"]:
            # 判斷是否是相對路徑模式
            url = None
            if wallpaper["image"].startswith("./") :
                url = f"https://colopl.co.jp{WCatNews[index]["link"]}{wallpaper["image"][2:]}"
            else :
                url = f"https://colopl.co.jp{wallpaper["image"]}"
            download_file(url, save_directory=f"downloads\\{sanitize_filename(WCatNews[index]["title"])}")
            print(url)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Fetch wallpaper by ID")
    parser.add_argument(
        "-id", type=int, required=False, help="The ID of the wallpaper to fetch"
    )
    args = parser.parse_args()
    
    asyncio.run(getWCatWallpaper(args.id))
