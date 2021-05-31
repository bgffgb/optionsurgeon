from scipy.integrate import quad
from scipy.special import betainc, beta
import numpy as np
import time

import logging

logger = logging.getLogger(__name__)

PROB_TH = 0.01

def modded_sgt(x, mu, sigma, lam):
    p = 2
    q = 2
    v = q**(-1/p) * ((3*lam**2 + 1)*(beta(3/p, q - 2/p)/beta(1/p,q)) - 4*lam**2*(beta(2/p, q - 1/p)/beta(1/p,q))**2)**(-1/2)
    m = 2*v*sigma*lam*q**(1/p)*beta(2/p,q - 1/p)/beta(1/p,q)
    fx = p  / (2*v*sigma*q**(1/p)*beta(1/p,q)*(abs(x-mu+m)**p/(q*(v*sigma)**p)*(lam*np.sign(x-mu+m)+1)**p + 1)**(1/p + q))
    return fx


class Distribution:
    def __init__(self, type, params):
        self.type = type
        self.params = [float(p) for p in params]
        self.mean_reference = 0
        self.steps = 200
        self.min_strike = 0
        self.max_strike = 100000
        self.mean_shift = 0
        self.var_level = 1
        self.minlim = 0
        self.maxlim = 100000
        self.cache = {}

        # Some custom magic needed for MSGT
        if self.type == "MSGT":
            self.norm, _ = quad(modded_sgt, -np.inf, np.inf, args=(self.params[0], self.params[1], self.params[2]))
            self.minlim = max(0, self.params[0] - 5 * self.params[1])
            self.maxlim = max(10 * self.params[0], self.params[0] + 10 * self.params[1])
            dx = 100
            self.interpolated_strikes = np.arange(self.minlim, self.maxlim, 1 / dx)
            self.prob_array = modded_sgt(self.interpolated_strikes, *self.params) / dx
            self.cumulative = np.cumsum(self.prob_array)

        self.adjust_min_strike()
        self.adjust_max_strike()

        self.mean_reference = self.solve_lower_bound(0.5)
        self.mean_shift_reference = (self.max_strike - self.min_strike)

    def solve_lower_bound(self, th):
        lower = self.minlim
        upper = self.maxlim
        while lower <= upper:
            mid = (lower + upper) / 2
            prob = self.get_cumulative(mid)
            if prob < th:
                lower = mid + 0.01
            else:
                upper = mid - 0.01
        return mid

    def solve_upper_bound(self, th, mode="cumulative"):
        lower = self.minlim
        upper = self.maxlim
        while lower <= upper:
            mid = (lower + upper) / 2
            prob = self.get_cumulative(mid)
            if prob < 1 - th:
                lower = mid + 0.01
            else:
                upper = mid - 0.01
        return mid

    def adjust_min_strike(self):
        self.min_strike = self.solve_lower_bound(PROB_TH)

    def adjust_max_strike(self):
        self.max_strike = self.solve_upper_bound(PROB_TH)

    def set_mean_shift_level(self, level):
        amount = level * 0.02 * self.mean_shift_reference
        self.mean_shift = amount
        self.cache = {}

    def set_var_shift_level(self, level):
        scale = 0.9 ** level
        self.var_level = scale
        self.cache = {}

    def get_mean(self):
        if self.type == 'F':
            return (self.params[2] / (self.params[2] - 2)) * self.params[0]
        if self.type == 'FF':
            m1 = (self.params[2] / (self.params[2] - 2)) * self.params[0]
            m2 = (self.params[5] / (self.params[5] - 2)) * self.params[3]
            r = self.params[6]
            return r * m1 + (1 - r) * m2

    def get_cumulative(self, x):
        if x in self.cache:
            return self.cache[x]
        x = (x - self.mean_reference) * self.var_level + self.mean_reference + self.mean_shift
        if self.type == 'F':
            scale, d1, d2 = self.params
            bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
            ba = d1 / 2
            bb = d2 / 2
            val = betainc(ba, bb, bx)
        if self.type == 'FF':
            scale, d1, d2, scaleB, d1B, d2B, r = self.params
            bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
            ba = d1 / 2
            bb = d2 / 2
            bx2 = d1B * (x / scaleB) / (d1B * (x / scaleB) + d2B)
            ba2 = d1B / 2
            bb2 = d2B / 2
            val = r * betainc(ba, bb, bx) + (1 - r) * betainc(ba2, bb2, bx2)
        if self.type == 'N':
            ind = np.searchsorted(self.params[0], x)
            st0 = self.params[0][ind - 1]
            st1 = self.params[0][ind]
            pr0 = self.params[1][ind - 1]
            pr1 = self.params[1][ind]
            r = (x - st0) / (st1 - st0)
            val = (1 - r) * pr0 + r * pr1
        if self.type == 'MSGT':
            val, err = quad(modded_sgt, 0, x, args=(self.params[0], self.params[1], self.params[2]))
            val /= self.norm

        if np.isnan(val):
            val = 1e-12

        # Cache + return
        self.cache[x] = val
        return val

    def get_probability(self, x, strike_lower=0, strike_higher=100000):
        x_min = (strike_lower + x) / 2
        x_max = (strike_higher + x) / 2
        if self.type == 'F':
            prob = self.get_cumulative(x_max) - self.get_cumulative(x_min)
            return prob
        if self.type == 'FF':
            prob = self.get_cumulative(x_max) - self.get_cumulative(x_min)
            return prob
        if self.type == 'N':
            prob = self.get_cumulative(x_max) - self.get_cumulative(x_min)
            return prob
        if self.type == 'MSGT':
            prob, _ = quad(modded_sgt, x_min, x_max, args=(self.params[0], self.params[1], self.params[2]))
            prob /= self.norm
            return prob

    def get_prob_arrays(self, steps=400, th_lower=None, th_upper=None, strike_min=None, strike_max=None):        
        if th_lower is not None:
            strike_min_th = self.solve_lower_bound(th_lower)
            if strike_min is None:
                strike_min = strike_min_th
            else:
                strike_min = min(strike_min, strike_min_th)

        if th_upper is not None:
            strike_max_th = self.solve_upper_bound(th_upper)
            if strike_max is None:
                strike_max = strike_max_th
            else:
                strike_max = max(strike_max, strike_max_th)

        strikes = np.arange(strike_min, strike_max, (strike_max - strike_min) / steps)
        prob_array, cum_array = [0], []
        for i in range(1, len(strikes) - 1):
            prob = self.get_probability(strikes[i], strikes[i - 1], strikes[i + 1])
            prob_array.append(prob)
            cum = self.get_cumulative(strikes[i]) - self.get_cumulative(strikes[i - 1])
            cum_array.append(cum)
        prob_array.append(0)
        return strikes, prob_array, cum_array

    def to_dict_array(self, steps=None):
        strikes, prob_array, cum_array = self.get_prob_arrays(steps=steps, strike_min=self.min_strike, strike_max=self.max_strike)
        probs = []
        for (strike, prob, cum) in zip(strikes, prob_array, cum_array):
            probs.append({'x' : strike, 'y' : prob, 'c' : "{:.2f}".format(cum * 100)})
        return probs
