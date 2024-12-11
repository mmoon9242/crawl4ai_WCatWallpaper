import asyncio
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

import re

import os
import requests

import argparse

DEBUG = True

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
    print(f"Download... {url}")
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {url}")
    else:
        print(f"Download error, error code: {response.status_code}")


async def getWCatWallpaper(WCatNewsUrl, startIndex=None, endIndex=None):
    print("WCat News Url: ", WCatNewsUrl)
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
        "baseSelector": "li.p-wallpaper__listItem, div.wpArea li, li.motion, li.wallpaper__listItem, .wp__list li, .fade_Up li, .wrap ul, li.c-wallpaperList__item, li.list__item",
        "fields": [
            {
                "name": "wallpaper",
                "type": "nested_list",
                "selector": "li.p-wallpaper__linksItem, div.link p, div.wallpaper__download p, .list__item-downloadBtn p, .wallpaper__listDownload p, .downloadBtn, .c-wallpaperList__download p, .wp__linkWrap p, .item__link li",
                "fields": [
                    {"name": "size", "selector": "a, a p", "type": "text"},
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
    print(json.dumps(WCatNews[0]["news"], indent=2, ensure_ascii=False))

    for index in range(startIndex, endIndex):

        print("\n\n\n\n\n")
        print(json.dumps(WCatNews[0]["news"][index], indent=2, ensure_ascii=False))

        WCatPageUrl = None
        # DONE: 修正URL會串錯
        # DONE: 修正http://開頭無法抓取到的問題
        if WCatNews[0]["news"][index]["link"].startswith(("https://", "http://")) :
            # FIXME: 有的網址最後一個字元是/，須要移除
            # NOTE: 如果是完整網址，就直接寫入WCatPageUrl
            WCatPageUrl = WCatNews[0]["news"][index]["link"]
            # NOTE: 判斷WCatPageUrl有沒有包含C社網域
            if not WCatPageUrl.startswith("https://colopl.co.jp") :
                # DONE: 修正使用break，會跳出整個迴圈，須改用continue
                print("不是C社網址")
                continue
        else :
            WCatPageUrl = f'https://colopl.co.jp{WCatNews[0]["news"][index]["link"]}'
        
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=WCatPageUrl,
                extraction_strategy=extractionStrategyWallpapers,
                bypass_cache=True,
            )
            assert result.success, "WCat Wallpapers error."
            WCatWallpapers = json.loads(result.extracted_content)

        savePath = f'{WCatNews[0]["news"][index]["date"]}_{sanitize_filename(WCatNews[0]["news"][index]["title"])}'

        if find_similar_dirs(f"downloads\\", savePath):
            print("已下載過，如要重新下載請刪除該目錄")
            # DONE: 修正使用break，會跳出整個迴圈，須改用continue
            continue

        print(json.dumps(WCatWallpapers, indent=2, ensure_ascii=False))

        for Wallpapers in WCatWallpapers:
            for wallpaper in Wallpapers["wallpaper"]:
                # NOTE: 判斷是否是相對路徑模式
                url = None
                
                if wallpaper["image"].startswith("./"):
                    # DONE: 預防性修正網址串接錯誤問題
                    # NOTE: 如果有找到./，那就是使用相對目錄
                    if WCatNews[0]["news"][index]["link"].startswith("https://colopl.co.jp"):
                        # NOTE: 如果開頭有網域了，就不再加一次
                        url = f'{WCatNews[0]["news"][index]["link"]}{wallpaper["image"][2:]}'
                    else :
                        # NOTE: 反之
                        url = f'https://colopl.co.jp{WCatNews[0]["news"][index]["link"]}{wallpaper["image"][2:]}'
                elif wallpaper["image"].startswith("/"):
                    # NOTE: 如果有找到/，那就是基於網址的絕對目錄
                    url = f'https://colopl.co.jp{wallpaper["image"]}'
                else:
                    # DONE: 修正網址串接錯誤問題
                    # NOTE: 如果開頭什麼都沒找到，那就是基於目前目錄的相對目錄，與./處理方式相同，但不需要去除前兩個字元
                    if WCatNews[0]["news"][index]["link"].startswith("https://colopl.co.jp"):
                        # NOTE: 如果開頭有網域了，就不再加一次
                        url = f'{WCatNews[0]["news"][index]["link"]}{wallpaper["image"]}'
                    else :
                        # NOTE: 反之
                        url = f'https://colopl.co.jp{WCatNews[0]["news"][index]["link"]}{wallpaper["image"]}'
                download_file(url,save_directory=f"downloads\\{savePath}")


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
            # "https://colopl.co.jp/shironekoproject/news/index_2.php",
            # "https://colopl.co.jp/shironekoproject/news/index_3.php",
            # "https://colopl.co.jp/shironekoproject/news/index_4.php",
            # "https://colopl.co.jp/shironekoproject/news/index_5.php",
            # "https://colopl.co.jp/shironekoproject/news/index_6.php",
            # "https://colopl.co.jp/shironekoproject/news/index_7.php",
            # "https://colopl.co.jp/shironekoproject/news/index_8.php",
            # "https://colopl.co.jp/shironekoproject/news/index_9.php",
            # "https://colopl.co.jp/shironekoproject/news/index_10.php",
            "https://colopl.co.jp/shironekoproject/news/index_11.php",
        ]
        for WCatNewsUrl in WCatNewsUrlList:
            asyncio.run(getWCatWallpaper(WCatNewsUrl, 0, 20))