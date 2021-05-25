from html.parser import HTMLParser
from .options import Option, OptionChain

import requests


def has_class_pattern(arr, pattern):
    for (tag, val) in arr:
        if tag == 'class' and pattern in val:
            return True
        return False


def is_class_empty(arr):
    if len(arr) == 0:
        return True

    for (tag, val) in arr:
        if tag == 'class' and val == '':
            return True
        return False


class MWTableHTMLParser(HTMLParser):
    ORDER = ['WAIT', 'CALL_LAST', 'CALL_CHANGE', 'CALL_BID', 'CALL_ASK', 'CALL_VOL', 'CALL_OI',
             'STRIKE', 'PUT_LAST', 'PUT_CHANGE', 'PUT_BID', 'PUT_ASK', 'PUT_VOL', 'PUT_OI']

    def __init__(self):
        super().__init__()
        self.process = False
        self.status_index = 0
        self.strike_on = False
        self.options = OptionChain()
        self.keyword_dict = {}
        self.target_date_str = ''
        self.dates = []
        self.current_price_warning = False

    def feed(self, data, target):
        self.target_date_str = target
        return super().feed(data)

    def push_keyword_dict(self):
        if len(self.keyword_dict) <= 1:
            return

        if 'CALL_LAST' in self.keyword_dict:
            # Add Call option
            self.options.add_option(Option(last=self.keyword_dict['CALL_LAST'],
                                           change=self.keyword_dict['CALL_CHANGE'],
                                           vol=self.keyword_dict['CALL_VOL'],
                                           bid=self.keyword_dict['CALL_BID'],
                                           ask=self.keyword_dict['CALL_ASK'],
                                           oi=self.keyword_dict.get('CALL_OI', 0),
                                           strike=self.keyword_dict['STRIKE'],
                                           type='CALL'))
        if 'PUT_LAST' in self.keyword_dict:
            # Add Put option
            self.options.add_option(Option(last=self.keyword_dict['PUT_LAST'],
                                           change=self.keyword_dict['PUT_CHANGE'],
                                           vol=self.keyword_dict['PUT_VOL'],
                                           bid=self.keyword_dict['PUT_BID'],
                                           ask=self.keyword_dict['PUT_ASK'],
                                           oi=self.keyword_dict.get('PUT_OI', 0),
                                           strike=self.keyword_dict['STRIKE'],
                                           type='PUT'))

    def reset_status(self):
        self.status_index = 0
        self.keyword_dict = {}
        self.strike_on = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and has_class_pattern(attrs, 'table'):
            # Start of new table --> disable reading until right date is hit
            self.process = False

        if self.process:
            if tag == 'tr' and has_class_pattern(attrs, 'table__row'):
                self.push_keyword_dict()
                self.reset_status()
            elif tag == 'td' and (is_class_empty(attrs) or has_class_pattern(attrs, 'in-money')):
                self.status_index += 1
            elif tag == 'td' and has_class_pattern(attrs, 'strike'):
                self.status_index = self.ORDER.index('STRIKE')
                self.strike_on = True

    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.process = False
            self.push_keyword_dict()
            self.reset_status()

    def handle_data(self, data):
        # Need this to get current price
        if data.startswith("Current price as of"):
            self.current_price_warning = True
            return
        if self.current_price_warning:
            data = data.strip()
            if len(data) == 0:
                return
            self.current_price_warning = False
            self.options.set_underlying(float(data[1:]))
            return

        # Turn scraping on for correct table only
        if self.target_date_str in data:
            self.process = True

        if self.process:
            stripped_data = data.strip().replace(',', '')
            if self.status_index > 0 and len(stripped_data) > 0:
                try:
                    nr_data = float(stripped_data)
                    self.keyword_dict[self.ORDER[self.status_index]] = nr_data
                except ValueError as e:
                    pass


def scrape_option_prices(ticker, month, year, date, type='stock'):
    # New Marketwatch URL pattern
    url = "https://www.marketwatch.com/investing/"+type+"/" + ticker + "/optionstable?optionMonth=" + month + "&optionYear=" + year + "&partial=true"
    res = requests.get(url)
    parser = MWTableHTMLParser()
    parser.feed(res.text, date)
    return parser.options
