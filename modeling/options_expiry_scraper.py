from html.parser import HTMLParser

import requests


def has_attr(arr, attr):
    for (tag, val) in arr:
        if tag == attr:
            return True
    return False


class MWDatesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.process = False
        self.dates = []

    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            if has_attr(attrs, 'data-tab-pane'):
                self.process = True

    def handle_endtag(self, tag):
        if tag == 'li':
            self.process = False

    def handle_data(self, data):
        if self.process:
            self.dates.append(data)

class MWExpiryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.process = False
        self.dates = []

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            if has_attr(attrs, 'data-tab-pane'):
                self.process = True

    def handle_endtag(self, tag):
        if tag == 'span':
            self.process = False

    def handle_data(self, data):
        if data.startswith('Expires'):
            self.dates.append(data[len('Expires '):])

def scrape_option_dates(ticker, type='stock'):
    url = "https://www.marketwatch.com/investing/"+type+"/" + ticker + "/options?mod=mw_quote_tab"
    res = requests.get(url)
    parser = MWDatesParser()
    parser.feed(res.text)

    # Double check ticker type
    if "fund/" + ticker.lower() + "/options" in res.text:
        type = "fund"

    return parser.dates, type

def scrape_option_expiries(ticker, month, year, type='stock'):
    url = "https://www.marketwatch.com/investing/"+type+"/" + ticker + "/optionstable?optionMonth=" + month + "&optionYear=" + year + "&partial=true"
    res = requests.get(url)
    parser = MWExpiryParser()
    parser.feed(res.text)
    return parser.dates
