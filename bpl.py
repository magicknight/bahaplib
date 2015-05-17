#!/usr/bin/env python3
""" A 巴哈姆特(https://forum.gamer.com.tw/) post library for python.
For more documentation, see README.md . """

import requests
import urllib.parse as urlparse
from bs4 import BeautifulSoup
import re

REQHEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36"}
REQCOOKIES = {}

def from_url(inurl):
    """ Initiates a bpl object (BahaPost or Floor) with an URL """
    parsed = urlparse.urlparse(inurl)
    params = dict(urlparse.parse_qsl(parsed.query))

    if (parsed.scheme == "http" and
            parsed.netloc == "forum.gamer.com.tw" and
            parsed.path == "/C.php" and
            all(x in params for x in ["bsn", "snA"])):
        return BahaPost(params["bsn"], params["snA"])
    elif (parsed.scheme == "http" and
          parsed.netloc == "forum.gamer.com.tw" and
          parsed.path == "/Co.php" and
          all(x in params for x in ["bsn", "sn"])):
        return Floor(params["bsn"], params["sn"])
    else:
        raise ValueError("Input is not a vaild bahaurl.")

def set_cookies(bahaid, baharune):
    """ Set baha cookies into global const. """
    global REQCOOKIES
    if len(baharune) == 84:
        REQCOOKIES = {"BAHAID": bahaid, "BAHARUNE": baharune}
    else:
        raise ValueError('Input is not a vaild baharune.')
    return None

class BahaPost:
    """ An object class used to describe a baha post. """
    def __init__(self, bsn, sna):
        """ Initiates a BahaPost object """
        self.bsn = bsn
        self.sna = sna
        self.url = ("http://forum.gamer.com.tw/C.php?" +
                    "bsn=" + str(self.bsn) + "&" + "snA=" + str(self.sna))

    @property
    def floors_snb(self):
        """ snb list of the BahaPost """
        ret = []

        soup = BeautifulSoup(
            requests.get("http://forum.gamer.com.tw/C.php",
                         params={"bsn": self.bsn, "snA": self.sna},
                         headers=REQHEADERS,
                         cookies=REQCOOKIES).text
        )

        for gpword in soup("a", {"class": "GPword"}):
            ret.append(
                re.search(r'upgp_(\d+)', gpword.attrs["id"]).group(1))

        return ret

    @property
    def floors(self):
        """ Floor object list of the BahaPost """
        ret = []

        for snb in self.floors_snb:
            ret.append(
                Floor(self.bsn, snb))
        return ret

    @property
    def content(self):
        """ The content of the main floor
        An alias for html
        """
        return self.floors[0].html

    @property
    def html(self):
        """ The content of the main floor in HTML """
        return self.floors[0].get_content(baha_code=False, prettify=True)

    @property
    def baha_code(self):
        """ The content of the main floor in baha_code, from /post1.php
        Requies vaild BAHARUNE and BAHAID cookies."""
        return self.floors[0].get_content(baha_code=True, prettify=False)

class Floor:
    """ An object class used to describe floors of baha posts """
    def __init__(self, bsn, snb):
        """ Initiates a floor object """
        self.bsn = str(bsn)
        self.snb = str(snb)
        soup = BeautifulSoup(requests.get("http://forum.gamer.com.tw/Co.php",
                                          params={"bsn": bsn, "sn": snb},
                                          headers=REQHEADERS,
                                          cookies=REQCOOKIES).text)

        for p_item in soup(id="BH-master")[0]("p", {"class": "FM-lbox1"}):
            parsed = urlparse.urlparse(p_item.a.attrs["href"])
            params_ = dict(urlparse.parse_qsl(parsed.query))
            if parsed.path == 'switch.php' and "bsn" in params_:
                self.sna = params_["snA"]
                break

    @property
    def content(self):
        """ The floor's content in html
        An alias for html """
        return self.html

    @property
    def html(self):
        """ The floor's content in baha_code, from /Co.php """
        return self.get_content(baha_code=False, prettify=True)

    @property
    def baha_code(self):
        """ The floor's content in baha_code, from /post1.php
        Requies vaild BAHARUNE and BAHAID cookies. """
        return self.get_content(baha_code=True, prettify=False)


    def get_content(self, baha_code=False, prettify=True):
        """ Retrieve content of a floor

        @param bool baha_code        Outputs baha_code from /post1.php when this is set to True,
                                    If not, Output HTML from /Co.php .
        @param bool prettify        Outputs prettified HTML by BeautifulSoup if is set.
        """

        if baha_code and not prettify:
            try:
                response = requests.get("http://forum.gamer.com.tw/post1.php",
                                        params={"bsn": self.bsn,
                                                "snA": self.sna,
                                                "sn": self.snb,
                                                "type": "2", "re": "1"},
                                        headers=REQHEADERS,
                                        cookies=REQCOOKIES)
                response.encoding = 'utf8'
                soup = BeautifulSoup(response.text)
                return re.search(r"^,bahacode:true,content:'([^']*?)'",
                                 str(soup(id="form1")[0].find_all("script")),
                                     flags=re.MULTILINE).group(1)
            except IndexError:
                raise Exception('Not authencated. Set cookies by bpl.set_cookies(BAHAID, BAHARUNE) .')
        elif baha_code and prettify:
            raise ValueError('baha_code and prettify can\'t be true at the same time')
        else:
            try:
                response = requests.get("http://forum.gamer.com.tw/Co.php",
                                        params={"bsn": self.bsn, "sn": self.snb},
                                        headers=REQHEADERS,
                                        cookies=REQCOOKIES)
                response.encoding = 'utf8'
                soup = BeautifulSoup(response.text)
                text = soup(id=("cf" + self.snb))[0]
                return text.prettify() if prettify else text.text
            except IndexError:
                raise Exception('Not found. The floor is probably deleted. Try retrieving baha_code.')
