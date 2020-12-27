import asyncio
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from selenium import webdriver
import json
import time
import random
import aiohttp
import asyncio
import pandas as pd
from collections import defaultdict as dd
from tqdm import tqdm
from fake_useragent import UserAgent
from selectolax.parser import HTMLParser


import threading
from queue import Queue
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType


def _get_proxies():
    with open("proxies") as f:
        return list(set([x for x in f.read().split("\n") if x != ""]))


input_file = "keyword.txt"
output_file = "fb_search_result.txt"
use_proxy = True
concurrency = 2
result = {}
proxies = _get_proxies()


def scraper(keyword):
    try:
        global result
        proxy = 'http://' + random.choice(proxies) if use_proxy else None
        driver_options = webdriver.FirefoxOptions()
        if use_proxy:
            driver_options.add_argument('--proxy-server=%s' % proxy)

        driver = webdriver.Firefox(executable_path="./geckodriver")

        # proxy_here = random.choice(proxies) if use_proxy else None
        # proxy = Proxy({
        #     'proxyType': ProxyType.MANUAL,
        #     'httpProxy': proxy_here,
        #     'ftpProxy': proxy_here,
        #     'sslProxy': proxy_here,
        #     'noProxy': ''
        # })
        # capabilities = webdriver.DesiredCapabilities.FIREFOX
        # proxy.add_to_capabilities(capabilities)
        # driver = webdriver.Firefox(
        #     executable_path="./geckodriver", desired_capabilities=capabilities)
            
        driver.implicitly_wait(2)
        url = "https://www.social-searcher.com/facebook-search" + "/?q=" + keyword
        driver.get(url)

        driver.execute_script("window.scrollTo(0, 200)")

        actions = ActionChains(driver)
        print(driver.find_element_by_css_selector(
            'div.gsc-selected-option-container.gsc-inline-block div.gsc-selected-option').text)
        select_element = driver.find_element_by_css_selector(
            'div.gsc-selected-option-container.gsc-inline-block')

        actions.click(select_element)
        actions.perform()

        select_element_in = driver.find_element_by_css_selector(
            'div.gsc-option-menu :nth-child(2) div.gsc-option')
        select_element_in.click()

        print(driver.find_element_by_css_selector(
            'div.gsc-selected-option-container.gsc-inline-block div.gsc-selected-option').text)
        html = driver.page_source

        result_set = set()

        def parse_html(html_source):
            for link in HTMLParser(html_source).css("a"):
                attrs = dd(lambda: None, link.attributes)
                if (
                    attrs["href"]
                    and "http" in attrs["href"]
                    and not "?" in attrs["href"]
                ):
                    result_set.add(attrs["href"])

        def set_page_number(number):
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight - 2000)")
            element = driver.find_element_by_xpath(
                "//div[@aria-label='Page " + str(number) + "']")
            element.click()
            return driver.page_source

        result.update({keyword: result_set})

        for i in range(10):
            if i != 0:
                parse_html(set_page_number(i + 1))
            else:
                parse_html(html)
    except:
        pass

    driver.close()


def output_result_segment(is_create=False):

    global result
    len_result = sum([len(item) for item in result.values()])
    print("total FB results found: ", len_result)

    option = 'a'
    if is_create:
        option = 'w'

    with open(output_file, option, encoding="utf-8") as out_file:
        for key in result:
            for item in result[key]:
                # out_file.write(key + '<--->' + item + '\n')
                out_file.write(item + '\n')
    
    result = {}


if __name__ == "__main__":
    with open(input_file) as f:
        keywords = [x for x in f.read().split("\n") if x != ""]

    is_create = True

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in tqdm(
            [keywords[x: x + concurrency]
             for x in range(0, len(keywords), concurrency)]
        ):
            try:
                loop = []
                for keyword in chunk:
                    loop.append(executor.submit(scraper, keyword))
                [None for thread in concurrent.futures.as_completed(loop)]

                # Do autosave whenever one loop end
                output_result_segment(is_create)

                is_create = False

            except Exception:
                print("one failed")
    output_result_segment()
