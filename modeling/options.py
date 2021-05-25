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

    def summary(self):
        return self.type + ' ' + str(self.strike) 

    def evaluate(self, strikes, probs, eval_type='MID', special=False):
        '''
        Returns expected returns, sharpe ratio and payout distribution 
        profit for this option, assuming it is held LONG (quantity = 1),
        for given strikes and their probability of happening
        '''
        returns = []
        expectation = 0
        norm = sum(probs)
        for (st, pr) in zip(strikes, probs):
            profit = self.get_profit(st, eval_type, special=special)
            expectation += profit * pr
            returns.append(profit)
        expectation /= norm
        stdev = 0
        for (ret, prob) in zip(returns, probs):
            stdev += prob/norm * ((ret - expectation) ** 2)
        stdev = stdev ** 0.5
        if stdev == 0:
            stdev, mean = 1, 0
        sharpe = expectation / stdev        

        return expectation, sharpe, returns

    def get_profit(self, stock_price, eval_type='MID', long=True, special=False):
        '''
        Returns profit for this option
        '''
        profit = 0

        if self.type == 'CALL' and stock_price > self.strike:
            profit += (stock_price - self.strike)
        if self.type == 'PUT' and stock_price < self.strike:
            profit += (self.strike - stock_price)
        
        if eval_type == 'MID':
            premium = -(self.bid + self.ask) / 2 # Premium paid for the option
        elif eval_type == 'ASK':
            premium = -self.ask  # Premium paid for the option
        elif eval_type == 'BID':
            premium = -self.bid  # Premium paid for the option

        refprofit = premium + profit
        if special:
            for r in [0.1, 0.5, 0.9]:
                premium = -self.get_premium(r)
                if abs(premium + profit) < abs(refprofit):
                    refprofit = premium + profit

        return 100 * refprofit

    def get_premium(self, r=0.5):
        return (self.bid * r  + self.ask * (1 - r)) # Premium from the deal


class OptionChain:
    def __init__(self):
        self.option_list = []
        self.ready = True
        self.call_strikes = []
        self.put_strikes = []
        self.strikes = []

    def set_underlying(self, val):
        self.underlying = val

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

    def get_call_table(self):
        sorted_table = []
        for _, calls in self.get_calls().items():
            for o in calls:
                sorted_table.append([o.strike, o.last, o.bid, o.ask, o.oi, o.vol, 0, 0])
        return sorted_table

    def get_put_table(self):
        sorted_table = []
        for _, puts in self.get_puts().items():
            for o in puts:
                sorted_table.append([o.strike, o.last, o.bid, o.ask, o.oi, o.vol, 0, 0])
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
