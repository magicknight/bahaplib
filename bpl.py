#!/usr/bin/env python3
""" A 巴哈姆特(https://forum.gamer.com.tw/) post library for python.
For more documentation, see README.md . """

import requests
import urllib.parse as urlparse
from bs4 import BeautifulSoup
import re
import bplcookies # Please input your own BAHAID and BAHARUNE cookies.

REQHEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36"}
REQCOOKIES = {"BAHAID": bplcookies.BAHAID, "BAHARUNE": bplcookies.BAHARUNE}

class bahaPost:
    """ An object class used to describe a baha post. """
    def __init__(self, bsn, snA):
        """ Initiates a bahaPost object """
        self.bsn = bsn
        self.snA = snA
        self.url = "http://forum.gamer.com.tw/C.php?" + "bsn=" + str(self.bsn) + "&" + "snA=" + str(self.snA)

    def from_url(inurl):
        """ Initiates a bahapost object with an URL """
        parsed = urlparse.urlparse(inurl)
        params = dict(urlparse.parse_qsl(parsed.query))

        if (parsed.scheme == "http" and
                parsed.netloc == "forum.gamer.com.tw" and
                parsed.path == "/C.php" and
                all(x in params for x in ["bsn", "snA"])):
            return bahaPost(params["bsn"], params["snA"])
        else:
            raise ValueError("Input is not a vaild bahaurl.")

    @property
    def floors_snB(self):
        """ snB list of the bahapost """
        ret = []

        soup = BeautifulSoup(
            requests.get( "http://forum.gamer.com.tw/C.php",
                    params = {"bsn": self.bsn, "snA": self.snA},
                    headers=REQHEADERS,
                    cookies=REQCOOKIES).text
        )

        for gpword in soup.body("a", {"class": "GPword"}):
            ret.append(
                    re.search("upgp_(\d+)", gpword.attrs["id"]).group(1))

        return ret

    @property
    def floors(self):
        """ Floor object list of the bahapost """
        ret = []

        for snB in self.floors_snB:
            ret.append(
                    floor(self.bsn, snB))
        return ret

    @property
    def content(self):
        """ The content of the main floor
        an alias for html
        """
        return self.floors[0].html

    @property
    def html(self):
        """ The content of the main floor in HTML """
        return self.floors[0].getContent(bahaCode=False, prettify=True)

    @property
    def bahacode(self):
        """ The content of the main floor in bahacode, from /post1.php
        Requies vaild BAHARUNE and BAHAID cookies."""
        return self.getContent(bahaCode=True, prettify=False)

class floor:
    """ An object class used to describe floors of baha posts """
    def __init__(self, bsn, snB):
        """ Initiates a floor object """
        self.bsn = bsn
        self.snB = snB
        soup = BeautifulSoup(requests.get("http://forum.gamer.com.tw/Co.php",
            params = {"bsn": bsn, "sn": snB},
            headers=REQHEADERS,
            cookies=REQCOOKIES).text)

        for p in soup(id="BH-master")[0]("p", {"class": "FM-lbox1"}):
            parsed = urlparse.urlparse(p.a.attrs["href"])
            params_ = dict(urlparse.parse_qsl(parsed.query))
            if parsed.path == 'switch.php' and "bsn" in params_:
                self.bsn = params_["bsn"]
                break

    def from_url(inurl):
        """ Initiate a floor object with an URL """
        parsed = urlparse.urlparse(inurl)
        params = dict(urlparse.parse_qsl(parsed.query))

        if (parsed.scheme == "http" and
                parsed.netloc == "forum.gamer.com.tw" and
                parsed.path == "/Co.php" and
                all(x in params for x in ["bsn", "sn"])):
            return floor(params["bsn"], params["sn"])
        else:
            raise ValueError("Input is not a vaild bahaurl.")

    @property
    def content(self):
        return self.html

    @property
    def html(self):
        """ The floor's content in bahacode, from /Co.php """
        return self.getContent(bahaCode=False, prettify=True)

    @property
    def bahacode(self):
        """ The floor's content in bahacode, from /post1.php
        Requies vaild BAHARUNE and BAHAID cookies. """
        return self.getContent(bahaCode=True, prettify=False)

    def getContent(self, bahaCode=False, prettify=True):
        """ Retrieve content of a floor

        @param bool bahaCode     Outputs bahaCode from /post1.php when this is set to True, if not, Output HTML from /Co.php .
        @param bool prettify     Outputs prettified HTML by BeautifulSoup if is set.
        """

        if bahaCode and not prettify:
            response = requests.get("http://forum.gamer.com.tw/post1.php",
                params = {"bsn": self.bsn, "snA": self.snA, "sn": self.snB, "type": "2", "re": "1"},
                headers=REQHEADERS,
                cookies=REQCOOKIES)
            response.encoding = 'utf8'
            soup = BeautifulSoup(response.text)
            return re.search("^,bahacode:true,content:'[^']*'",
                    str(soup(id="form1")[0].find_all("script")),
                    multiline=True).group(1)
        elif bahaCode and prettify:
            raise ValueError('bahaCode and prettify can\'t be true at the same time')
        else:
            response = requests.get("http://forum.gamer.com.tw/Co.php",
                params = {"bsn": self.bsn, "sn": self.snB},
                headers=REQHEADERS,
                cookies=REQCOOKIES)
            response.encoding = 'utf8'
            soup = BeautifulSoup(response.text)
            return soup(id="cf"+ self.snB)[0].prettify() if prettify else soup(id="cf"+ self.snB)[0].content
