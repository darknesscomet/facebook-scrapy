import aiohttp
import asyncio
from selectolax.parser import HTMLParser
from collections import defaultdict as dd
import pandas as pd
from tqdm import tqdm
import random


class Scraper:
    def __init__(self, input_file, output_file, concurrency, use_proxy):
        self.input_file = input_file
        self.output_file = output_file
        self.result = []
        self.size = concurrency
        self.proxies = self._get_proxies()
        self.use_proxy = use_proxy

    def _get_proxies(self):
        with open("proxies") as f:
            return list(set([x for x in f.read().split("\n") if x != ""]))

    async def fetch(self, url, session):
        try:
            proxy = 'http://' + random.choice(self.proxies) if self.use_proxy else None
            url = 'http://' + url
            async with session.get(url, proxy=proxy) as response:
                html = await response.text()
                for link in HTMLParser(html).css("a"):
                    attrs = dd(lambda: None, link.attributes)
                    if (
                        attrs["href"]
                        and "facebook.com/" in attrs["href"]
                        and not "?" in attrs["href"]
                    ):
                        self.result.append({"url": url, "fb": attrs["href"]})
                        break

        except Exception:
            pass

    async def main(self, urls):
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"
            },
        ) as session:
            await asyncio.wait([self.fetch(url, session) for url in urls])

    def run(self):
        loop = asyncio.get_event_loop()

        with open(self.input_file) as f:
            urls = [x for x in f.read().split("\n") if x != ""]
        
        for chunk in tqdm(
            [urls[x : x + self.size] for x in range(0, len(urls), self.size)]
        ):
            try:
                loop.run_until_complete(self.main(chunk))
            except Exception:
                print("Chunk failed")

        print("total FB pages found: ", len(self.result))

        # df = pd.DataFrame(self.result)
        # df.to_csv(self.output_file, index=False)

        with open(self.output_file, 'w', encoding="utf-8") as output:
            for line in self.result:
                output.write(line['url'] + ' ' + line['fb'] + '\n')


if __name__ == "__main__":
    #Scraper(input_file="shopify3001.txt", output_file="shopifyrescan.csv", concurrency=10, use_proxy=False).run()
    Scraper(input_file="shopify3001.txt", output_file="fbpagediff.txt", concurrency=10, use_proxy=False).run()
