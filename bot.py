import time

import httpx

while True:
    print(httpx.get("http://www.google.com"))
    time.sleep(10)
