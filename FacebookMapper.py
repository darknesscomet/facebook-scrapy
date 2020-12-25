from fake_useragent import UserAgent
import pandas as pd
import aiohttp
import asyncio
import random
from tqdm import tqdm
import re


class FacebookMapper:
    def __init__(self, input_file, output_file, use_proxy, concurrency):
        self.input_file = input_file
        self.output_file = output_file
        self.batch_size = concurrency
        self.use_proxy = use_proxy
        self.ua = UserAgent()
        self.proxies = self._get_proxies()
        self.result = []

    def _get_proxies(self):
        with open("proxies") as f:
            return [x for x in f.read().split("\n") if x != ""]

    def _records(self):
        # df = pd.read_csv(self.input_file)
        # values = list(zip(df["fb"].values, df["url"].values))
        values = []
        with open(self.input_file, 'r') as input_file:
            for line in input_file.readlines():
                values.append(line.split())

        for chunk in tqdm(
            [
                values[i : i + self.batch_size]
                for i in range(len(values))[:: self.batch_size]
            ]
        ):
            random.shuffle(self.proxies)
            yield zip(chunk, self.proxies[: len(chunk)])

    def dump(self):
        df = pd.DataFrame(self.result)
        # df.to_csv(self.output_file, index=False)
        with open(self.output_file, 'w') as output:
            for line in self.result:
                output.write(line['url'] + ' ' + line['fb'] + ' ' +line['fb_id'] +'\n')
        print(len(df[df["fb_id"] != "not_found"]))

    async def get_id(self, session, x):
        try:
            fb, url = x[0]
            proxy = x[1]
            if not fb.startswith("http"):
                fb = "http://" + fb

            proxy = "http://" + proxy if self.use_proxy else None
            async with session.get(fb, proxy=proxy) as response:
                body = await response.text()
                body = body.split("entity_id")[-1][:30].split("}")[0]
                id = re.findall(r"\d{11,}", body)
                if id:
                    self.result.append({"fb": fb, "url": url, "fb_id": id[0]})
                else:
                    self.result.append({"fb": fb, "url": url, "fb_id": "not_found"})

        except Exception as e:
            self.result.append({"fb": fb, "url": url, "fb_id": "not_found"})

    async def main(self):
        headers = {
            "authority": "m.facebook.com",
            "upgrade-insecure-requests": "1",
            "user-agent": self.ua.random,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate",
        }

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for batch in self._records():
                await asyncio.wait([self.get_id(session, x) for x in batch])
                self.dump()

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())


if __name__ == "__main__":
    # FacebookMapper(
    #     input_file="fbpagediff.csv", output_file="outputfbpagediff.csv", use_proxy=True, concurrency=250
    # ).run()
    FacebookMapper(
        input_file="fbpagediff.txt", output_file="outputfbpagediff.txt", use_proxy=True, concurrency=250
    ).run()
