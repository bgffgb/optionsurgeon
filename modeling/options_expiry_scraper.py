from collections import OrderedDict
from html.parser import HTMLParser
import logging
import requests
import time
import yfinance as yf

logger = logging.getLogger(__name__)

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

month_to_short_name = {
    '01' : 'Jan',
    '02' : 'Feb',
    '03' : 'Mar',
    '04' : 'Apr',
    '05' : 'May',
    '06' : 'Jun',
    '07' : 'Jul',
    '08' : 'Aug',
    '09' : 'Sep',
    '10' : 'Oct',
    '11' : 'Nov',
    '12' : 'Dec',
}

month_short_to_long = {'Jan' : 'January', 'Feb' : 'February', 'Mar' : 'March',\
                 'Apr' : 'April', 'May' : 'May', 'Jun' : 'June', \
                 'Jul' : 'July', 'Aug' : 'August', 'Sep' : 'September', \
                 'Oct' : 'October', 'Nov' : 'November', 'Dec' : 'December',
}

def get_marketwatch_str(yahoo_expiry):
    year, month, day = yahoo_expiry.split('-')
    month_short = month_to_short_name[month]
    month_long = month_short_to_long[month_short]

    date = month_long + " " + year
    expiry = month_short + " " + day + ", " + year
    return date, expiry
    


def scrape_all_expiries(ticker):
    oh = yf.Ticker(ticker)
    expiries = oh.options

    # Convert it into Marketwatch format
    date_dict = OrderedDict()
    first_date = None
    first_exp = None
    for e in expiries:      
        date, mwexp = get_marketwatch_str(e)
        if date not in date_dict:
            date_dict[date] = []
        date_dict[date].append(mwexp)
        if first_exp is None:
            first_exp = mwexp
            first_date = date
    return date_dict, first_date, first_exp

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
