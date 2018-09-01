#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import re
from bs4 import BeautifulSoup
import sys
import os
import logging
import inspect
from selenium import webdriver
import json


def setUpLogger():
    # Create logger
    cf = inspect.currentframe()
    filename = inspect.getframeinfo(cf).filename
    filename = os.path.basename(filename)
    filename = os.path.splitext(filename)[0]
    logger = logging.getLogger(filename)
    logger.setLevel(logging.DEBUG)

    logger.addHandler(logging.NullHandler())
    logging.basicConfig(filename=filename + ".log", format='%(asctime)s: %(levelname)s> %(message)s')

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(levelname)s:%(name)s> %(message)s')

    # Add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return(logger)


def main():
    logger = setUpLogger()

    url = sys.argv[1]
    logger.debug("URL: {}".format(url))

    home = os.path.expanduser("~")

    # Using requests module to get webpage. Being detected as a bot occurs more frequently using this method
    # websites check if javascript is enabled, and requests has no javascript capability.
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36'}
    # web_page = requests.get(url, headers=headers).text

    driver = webdriver.Chrome()
    driver.get(url)

    web_page = driver.page_source

    soup = BeautifulSoup(web_page, "html.parser")
    printable_soup = soup.encode('ascii', 'ignore').decode('ascii')
    logger.debug("Page HTML: {}".format(printable_soup))

    javascript = soup.find_all('script', type="text/javascript")
    logger.debug("Extracted javascript: \n{}".format(javascript))

    try:
        # The regular expression searchs for "data[colorImages] = { .... };" and extracts the dictionary
        # portion { .... }.
        match = re.search('(data\[\"colorImages\"\]\s=\s{)(.*?)(;\n)', str(javascript))
        if match is not None:
            data = match.group(2)
            shirts = json.loads(data.encode('unicode_escape').decode())
        else:
            if isinstance(javascript, list):
                for script in javascript:
                    match = re.search('''var\sobj\s=\sjQuery.parseJSON\(\'(.*?)\'\)''', str(script))
                    if match is not None:
                        data = match.group(1)
                        data = json.loads(data.encode('unicode_escape').decode())
                        shirts = data['colorImages']
                        break
            else:
                match = re.search('''var\sobj\s=\sjQuery.parseJSON\(\'(.*?)\'\)''', str(javascript))
                if match is not None:
                    data = data.group(1)
                    data = json.loads(data.encode('unicode_escape').decode())
                    shirts = data['colorImages']
        logger.debug("Parsed shirt data:\n{}".format(shirts))
    except Exception as e:
        if printable_soup.find("not a robot") != -1:
            raise SystemExit("Amazon rejected HTML request because of bot detection.")

        logger.info(e)
        raise

    try:
        shirt_folder = home + "/Downloads/Amazon HiRes Shirts/"
        os.mkdir(shirt_folder)
    except:
        logger.debug("""The directory "~/Downloads/Amazon HiRes Shirts" already exists.""")

    for shirt in shirts:
        # Shirts dictionary follows this format:
        '''
        {"Women Heather Grey":
            [
                {"large":"...",
                "variant":"...",
                "hiRes":"hiRes url",
                "thumb":"...",
                }, ...
            ]
        '''
        url = shirts[str(shirt)][0]['hiRes']
        r = requests.get(url)
        if r.status_code == 200:
            with open(shirt_folder + shirt + ".png", 'wb') as f:
                f.write(r.content)

    print("Finished downloading images.")


if __name__ == '__main__':
    main()


## Example. attrs is used for non-standard tags.
# x = soup.find_all(class_='a-dynamic-image a-stretch-horizontal', attrs={'data-a-dynamic-image'})

# y = re.search('(https.*?)(\":)', str(x)).group(1)
# webbrowser.open(y)