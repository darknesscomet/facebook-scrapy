import asyncio
import concurrent.futures
import time
import random
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType


def _get_proxies():
    with open("proxies") as f:
        return list(set([x for x in f.read().split("\n") if x != ""]))


input_file = "video_keyword.txt"
output_file = "fb_video_result.txt"
use_proxy = False
concurrency = 2
result = []
proxies = _get_proxies()


def _url_encoding(key):
    result = ""
    for character in key:
        if character == '"':
            result += '%22'
        elif character == ' ':
            result += '%20'
        else:
            result += character
    return result


def parse_html(html_source, keyword):
    soup = BeautifulSoup(html_source, "html.parser")
    for link in soup.find_all('a'):
        if link.get("ajaxify") and "video" in link.get("aria-label").lower() and link.get("ajaxify") != "#":
            # print(link.get("ajaxify"))
            result.append({"keyword": keyword, "url": "https://www.facebook.com" + link.get("ajaxify")})


def scraper(keyword):
    try:
        global result
        proxy = 'http://' + random.choice(proxies) if use_proxy else None
        driver_options = webdriver.FirefoxOptions()
        if use_proxy:
            driver_options.add_argument('--proxy-server=%s' % proxy)

        driver = webdriver.Firefox(
            executable_path="./geckodriver", options=driver_options)

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
        driver.implicitly_wait(1)
        encoded_keyword = _url_encoding(keyword)
        url = "https://www.facebook.com/public?query=" + encoded_keyword + "&type=videos"
        print(url)

        driver.get(url)

        # after loding url sleep 2 seconds
        time.sleep(2)

        try:
            driver.find_element_by_xpath("//button[@id='u_0_h']").click()
            print("found popup")
        except:
            pass

        # whether popup appears or not, sleep 5 seconds
        time.sleep(5)

        # this value is used to determine the need of terminating
        compare = driver.page_source
        while True:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            
            # between scrolling sleep 2 seconds
            time.sleep(2)

            try:
                Div = driver.find_element_by_xpath(
                    "//div[@id='browse_end_of_results_footer']/div/div//div[@class='phm _64f']").text
            except:
                Div = "more result"
                try:
                    criteria = driver.find_element_by_xpath(
                        "//div[@id='u_0_1']/div/div/div/div/div/div/div/div/div").text[:29]
                    if criteria == "Non abbiamo trovato nulla per" or criteria == "We couldn't find anything for":
                        break
                except:
                    pass

            print(Div)
            if 'Fine dei risultati' == Div or 'End of results' == Div or 'End of Results' == Div:
                print("the end")
                break
            else:
                # determine the need of terminating
                if compare == driver.page_source:
                    print("we need to exit")
                    break
                else:
                    compare = driver.page_source
                continue

        parse_html(driver.page_source, keyword)
    except:
        pass
    driver.close()


def output_result_segment(is_create=False):

    global result
    print("total FB results found: ", len(result))

    option = 'a'
    if is_create:
        option = 'w'

    with open(output_file, option, encoding="utf-8") as output:
        for line in result:
            # output.write(line['keyword'] + '<--->' + line['url'] + '\n')
            output.write(line['url'] + '\n')
    

    result = []


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
