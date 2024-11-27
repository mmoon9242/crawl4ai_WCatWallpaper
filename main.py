import asyncio
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

import re

import os
import requests

import argparse


def write_single_line(file_path, content):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def is_line_equal(file_path, target_string):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line == target_string
    except FileNotFoundError:
        print(f"No log file: {file_path}")
        return False


def find_similar_dirs(base_dir, search_name):
    """
    搜尋目錄中名稱部分匹配的目錄
    :param base_dir: 目錄的基底路徑
    :param search_name: 要搜尋的部分名稱
    :return: 匹配的目錄列表
    """
    try:

        if not os.path.exists(base_dir):
            print(f"路徑不存在: {base_dir}")
            return []


        dirs = [
            d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))
        ]

        similar_dirs = [d for d in dirs if search_name in d]

        return similar_dirs

    except Exception as e:
        print(f"發生錯誤: {e}")
        return []


def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(invalid_chars, "-", filename)
    return sanitized_filename


def download_file(url, save_directory="."):
    filename = os.path.basename(url)
    # NOTE: 過濾掉儲存檔案名稱內的GET參數，原始url不改變
    save_path = os.path.join(save_directory, filename).split("?")[0]

    # 如果資料夾不存在，則建立一個資料夾
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Download: {url}")
    else:
        print(f"Download error, error code: {response.status_code}")


async def getWCatWallpaper(WCatNewsUrl, startIndex=None, endIndex=None):
    # NOTE: 先處理endIndex
    if endIndex != None:
        endIndex += 1
    # NOTE: 整頁抓取，並且獲取下一頁的連結
    schemaNews = {
        "name": "WCat News",
        "baseSelector": "body",
        "fields": [
            {
                "name": "news",
                "type": "list",
                "selector": "li.entry",
                "fields": [
                    {"name": "title", "selector": "h3.entryTitle", "type": "text"},
                    {
                        "name": "date",
                        "selector": "p.date",
                        "type": "regex",
                        "pattern": r"(\d{4}.\d{2}.\d{2})",
                    },
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
            },
            {
                "name": "nextPage",
                "selector": "a.link_next",
                "type": "attribute",
                "attribute": "href",
            },
        ],
    }
    extractionStrategyNews = JsonCssExtractionStrategy(schemaNews, verbose=True)
    schemaWallpapers = {
        "name": "WCat Wallpapers",
        "baseSelector": "li.p-wallpaper__listItem, div.wpArea li, li.motion.fadeInUp",
        "fields": [
            {
                "name": "wallpaper",
                "type": "nested_list",
                "selector": "li.p-wallpaper__linksItem, div.link p",
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
            url=WCatNewsUrl,
            extraction_strategy=extractionStrategyNews,
            bypass_cache=True,
        )
        assert result.success, "WCat News error."
        WCatNews = json.loads(result.extracted_content)

    # print(json.dumps(WCatNews[0]["news"], indent=2, ensure_ascii=False))
    print(f'Success, {len(WCatNews[0]["news"])} news')

    for index in range(startIndex, endIndex):

        print(json.dumps(WCatNews[0]["news"][index], indent=2, ensure_ascii=False))

        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=f'https://colopl.co.jp{WCatNews[0]["news"][index]["link"]}',
                extraction_strategy=extractionStrategyWallpapers,
                bypass_cache=True,
            )
            assert result.success, "WCat Wallpapers error."
            WCatWallpapers = json.loads(result.extracted_content)

        savePath = f'{WCatNews[0]["news"][index]["date"]}_{sanitize_filename(WCatNews[0]["news"][index]["title"])}'
        
        if find_similar_dirs(f"downloads\\",savePath) :
            print("目錄已經存在")
            print("目錄已經存在")
            print("目錄已經存在")
            print("目錄已經存在")
            print("目錄已經存在")
            print("目錄已經存在")
            print("目錄已經存在")
            print("目錄已經存在")
            
        if is_line_equal("news.txt", savePath) and index == 0:
            print("已下載過，未更新")
            None
        else:
            if index == 0:
                write_single_line("news.txt", savePath)

            print(json.dumps(WCatWallpapers, indent=2, ensure_ascii=False))

            for Wallpapers in WCatWallpapers:
                for wallpaper in Wallpapers["wallpaper"]:
                    # NOTE: 判斷是否是相對路徑模式
                    url = None
                    if wallpaper["image"].startswith("./"):
                        url = f'https://colopl.co.jp{WCatNews[0]["news"][index]["link"]}{wallpaper["image"][2:]}'
                    else:
                        url = f'https://colopl.co.jp{wallpaper["image"]}'
                    download_file(
                        url,
                        save_directory=f"downloads\\{savePath}",
                    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Fetch wallpaper by ID")
    parser.add_argument(
        "-start",
        type=int,
        required=False,
        help="The start index of the wallpaper to fetch",
    )
    parser.add_argument(
        "-end", type=int, required=False, help="The end index of the wallpaper to fetch"
    )

    args = parser.parse_args()

    startIndex = args.start
    endIndex = args.end

    if startIndex != None and endIndex != None:
        print(f"Args mode. Page 1, start index: {startIndex}, end index: {endIndex}.")
        asyncio.run(
            getWCatWallpaper(
                "https://colopl.co.jp/shironekoproject/news", startIndex, endIndex
            )
        )
    elif startIndex != None:
        print(f"Args mode. Page 1, start index: {startIndex}.")
        asyncio.run(
            getWCatWallpaper(
                "https://colopl.co.jp/shironekoproject/news", startIndex, startIndex
            )
        )
    else:
        print(f"Code list mode")
        WCatNewsUrlList = [
            # "https://colopl.co.jp/shironekoproject/news",
            "https://colopl.co.jp/shironekoproject/news/index_2.php",
            "https://colopl.co.jp/shironekoproject/news/index_3.php",
            "https://colopl.co.jp/shironekoproject/news/index_4.php",
            "https://colopl.co.jp/shironekoproject/news/index_5.php",
        ]
        for WCatNewsUrl in WCatNewsUrlList:
            asyncio.run(getWCatWallpaper(WCatNewsUrl, 0, 20))
