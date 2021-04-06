from collections import OrderedDict

class Option:
    def __init__(self, type, bid, ask, strike, last=0, change=0, vol=0, oi=0):
        self.last = last
        self.change = change
        self.vol = int(vol)
        self.oi = int(oi)
        self.bid = bid
        self.ask = ask
        self.strike = strike
        self.type = type

    def is_valid(self):
        if self.bid == 0 and self.ask == 0:
            return False
        return True

    def __str__(self):
        return self.type + ' ' + str(self.strike) + '$: Bid ' + str(self.bid) + ' Ask ' + str(self.ask) + ' Vol ' \
               + str(self.vol) + ' OI ' + str(self.oi) + ' Last ' + str(self.last)

    def get_profit(self, stock_price, eval_type='MID'):
        '''
        Returns profit fot this option, assuming it is held LONG (quantity = -1)
        '''
        if eval_type == 'MID':
            profit = (self.bid + self.ask) / 2 # Premium from the deal
        elif eval_type == 'ASK':
            profit = self.ask  # Premium paid for the deal
        elif eval_type == 'BID':
            profit = self.bid  # Premium received for the deal

        if self.type == 'CALL' and stock_price > self.strike:
            profit += (self.strike - stock_price)
        if self.type == 'PUT' and stock_price < self.strike:
            profit += (stock_price - self.strike)

        return -100 * profit

    def get_premium(self):
        return (self.bid + self.ask) / 2 # Premium from the deal


class OptionChain:
    def __init__(self):
        self.option_list = []
        self.ready = True
        self.call_strikes = []
        self.put_strikes = []
        self.strikes = []

    def add_option(self, o : Option):
        if not o.is_valid():
            # Can't trust it
            return

        self.option_list.append(o)
        if o.strike not in self.strikes:
            self.strikes.append(o.strike)
        if o.type == 'CALL' and o.strike not in self.call_strikes:
            self.call_strikes.append(o.strike)
        if o.type == 'PUT' and o.strike not in self.put_strikes:
            self.put_strikes.append(o.strike)
        self.ready = False

    def make_sorted(self):
        self.strikes.sort()
        self.call_strikes.sort()
        self.put_strikes.sort()
        self.ready = True

    def get_strikes(self):
        if not self.ready:
            self.make_sorted()
        return self.strikes

    def get_call_strikes(self):
        if not self.ready:
            self.make_sorted()
        return self.call_strikes

    def get_put_strikes(self):
        if not self.ready:
            self.make_sorted()
        return self.put_strikes

    def get_table(self):
        nrc = 5
        table = {}
        for st in self.get_strikes():
            if st not in table:
                table[st] = [' ' for i in range(2 * nrc + 1)]
                table[st][nrc] = st
        for op in self.option_list:
            shift = 0
            st = op.strike
            if op.type == 'PUT':
                shift = nrc + 1

            table[st][shift] = op.last
            table[st][shift + 1] = op.bid
            table[st][shift + 2] = op.ask
            table[st][shift + 3] = op.oi
            table[st][shift + 4] = op.vol

        sorted_table = []
        for st in sorted(table.keys()):
            sorted_table.append(table[st])
        return sorted_table

    def get_options(self):
        if not self.ready:
            self.make_sorted()
        res = OrderedDict()
        for st in self.get_strikes():
            res[st] = []
        for o in self.option_list:
            res[o.strike].append(o)
        return res

    def get_calls(self):
        if not self.ready:
            self.make_sorted()
        res = OrderedDict()
        for st in self.get_call_strikes():
            res[st] = []
        for o in self.option_list:
            if o.type == 'CALL':
                res[o.strike].append(o)
        return res

    def get_puts(self):
        if not self.ready:
            self.make_sorted()
        res = OrderedDict()
        for st in self.get_put_strikes():
            res[st] = []
        for o in self.option_list:
            if o.type == 'PUT':
                res[o.strike].append(o)
        return res

    def print(self):
        if not self.ready:
            self.make_sorted()
        for o in self.option_list:
            print(o)
