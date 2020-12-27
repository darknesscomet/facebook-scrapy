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


input_file = "watch_keyword.txt"
output_file = "fb_watch_result.txt"
use_proxy = True
concurrency = 2
result = []
proxies = _get_proxies()


def parse_html(html_source, keyword):
    soup = BeautifulSoup(html_source, "html.parser")
    for link in soup.find_all('a'):
        if link.get("href") and "video" in link.get("href").lower() and link.get("href") != "#":
            result.append({"keyword": keyword, "url": "https://www.facebook.com" + link.get("href")})


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
        url = "https://www.facebook.com/watch/search/?query=" + keyword
        driver.get(url)

        # after loding url sleep 2 seconds
        time.sleep(2)

        try:
            driver.find_element_by_xpath("//button[@id='u_0_j']").click()
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
                    "//div[@id='browse_end_of_results_footer']/div/div/div//div[@class='phm _64f']").text
            except:
                Div = "more result"
                try:
                    criteria = driver.find_element_by_xpath(
                        "//div[@id='u_0_c']/div/div/div/div/div/div/div/div/div").text[:29]
                    if criteria == "Non abbiamo trovato nulla per" or criteria == "We couldn't find anything for":
                        break
                except:
                    pass

            print(Div)
            if 'Fine dei risultati' == Div or 'End of Results' == Div or 'End of results' == Div:
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
