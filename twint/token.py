import re
import time
import os
import random
import requests
import logging as logme
from fake_useragent import UserAgent

class TokenExpiryException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

        
class RefreshTokenException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        

class Token:
    def __init__(self, config):
        self._session = requests.Session()
        #self._session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'})
        #self._session.headers.update({'User-Agent': })
        try:
            self.ua = UserAgent().firefox
        except Exception as e:
            print(e)
            self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"
        self._session.headers.update({'User-Agent': self.ua})
        self.config = config
        self._retries = 30
        self._timeout = 20
        self.url = 'https://twitter.com'

    def _request(self):
        for attempt in range(self._retries + 1):
            # The request is newly prepared on each retry because of potential cookie updates.
            req = self._session.prepare_request(requests.Request('GET', self.url))
            logme.debug(f'Retrieving {req.url}')
            if "proxy.txt" in os.listdir():
                print("load proxy")
                file = open("proxy.txt")
                proxy = random.choice(file.read().split('\n'))
                file.close()
                proxy_ = {"http":proxy,"https":proxy}
            else:
                print("proxy not used")
                proxy_ = None
            self.proxy = proxy_
            try:
                r = self._session.send(req, allow_redirects=True, timeout=self._timeout, proxies=proxy_)
            except requests.exceptions.RequestException as exc:
                if attempt < self._retries:
                    retrying = ', retrying'
                    level = logme.WARNING
                else:
                    retrying = ''
                    level = logme.ERROR
                logme.log(level, f'Error retrieving {req.url}: {exc!r}{retrying}{proxy_}')
            else:
                success, msg = (True, None)
                msg = f': {msg}' if msg else ''

                if success:
                    logme.debug(f'{req.url} retrieved successfully{msg}')
                    return r
            if attempt < self._retries:
                # TODO : might wanna tweak this back-off timer
                sleep_time = 2.0 * 2 ** attempt
                logme.info(f'Waiting {sleep_time:.0f} seconds')
                time.sleep(sleep_time)
        else:
            msg = f'{self._retries + 1} requests to {self.url} failed, giving up.'
            logme.fatal(msg)
            self.config.Guest_token = None
            raise RefreshTokenException(msg)

    def refresh(self):
        logme.debug('Retrieving guest token')
        res = self._request()
        match = re.search(r'\("gt=(\d+);', res.text)
        if match:
            logme.debug('Found guest token in HTML')
            self.config.Guest_token = str(match.group(1))
        else:
            self.config.Guest_token = None
            raise RefreshTokenException(f'Could not find the Guest token in HTML {self.proxy}{self.ua}')
