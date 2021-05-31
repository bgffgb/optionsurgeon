import numpy as np
from scipy.optimize import *
from scipy.special import betainc, beta

from .options import *
from .distribution import *

logger = logging.getLogger(__name__)

def add_call_bull_spreads(sorted_call_strikes, options_dict_calls, strikes, probs, D=2):
    N = len(sorted_call_strikes)
    for i in range(1, N):
        for j in range(max(0, i - D), i):
            strike0 = sorted_call_strikes[j]
            strike1 = sorted_call_strikes[i]
            mid_strike = (strike0 + strike1) / 2

            bullspread_premium = - options_dict_calls[strike0][0].get_premium() + \
                                 options_dict_calls[strike1][0].get_premium()
            #implied_prob = -bullspread_premium / (strike1 - strike0)
            implied_prob = (bullspread_premium / (strike1 - strike0)) + 1

            if implied_prob < 0:
                implied_prob = 0
            if implied_prob > 1:
                implied_prob = 1
            #print(mid_strike, implied_prob, bullspread_premium)
            strikes.append(mid_strike)
            probs.append(implied_prob)
    return strikes, probs


def add_put_bull_spreads(sorted_put_strikes, options_dict_puts, strikes, probs, D=2):
    N = len(sorted_put_strikes)
    for i in range(0, N - 1):
        for j in range(i + 1, min(N, i + D + 1)):
            strike0 = sorted_put_strikes[j]
            strike1 = sorted_put_strikes[i]
            mid_strike = (strike0 + strike1) / 2

            bullspread_premium = options_dict_puts[strike0][0].get_premium() - \
                                 options_dict_puts[strike1][0].get_premium()
            #implied_prob = (bullspread_premium / (strike1 - strike0)) + 1
            implied_prob = -bullspread_premium / (strike1 - strike0)

            if implied_prob < 0:
                implied_prob = 0
            if implied_prob > 1:
                implied_prob = 1
            strikes.append(mid_strike)
            probs.append(implied_prob)
    return strikes, probs


def modded_sgt(x, mu, sigma, lam):
    p = 2
    q = 2
    v = q**(-1/p) * ((3*lam**2 + 1)*(beta(3/p, q - 2/p)/beta(1/p,q)) - 4*lam**2*(beta(2/p, q - 1/p)/beta(1/p,q))**2)**(-1/2)
    m = 2*v*sigma*lam*q**(1/p)*beta(2/p,q - 1/p)/beta(1/p,q)
    fx = p  / (2*v*sigma*q**(1/p)*beta(1/p,q)*(abs(x-mu+m)**p/(q*(v*sigma)**p)*(lam*np.sign(x-mu+m)+1)**p + 1)**(1/p + q))
    return fx


def fit_MSGT(x, *args):
    strikes, probs = args

    minv = min(strikes)
    maxv = max(strikes)
    dx = 2
    interpolated_strikes = np.arange(minv - 1, maxv + 1, 1 / dx)
    prob_array = modded_sgt(interpolated_strikes, *x) / dx
    prob_array /= sum(prob_array)
    cumulative = np.cumsum(prob_array)
    toterr = 0
    for st, p in zip(strikes, probs):
        ind = np.searchsorted(interpolated_strikes, st)
        toterr += abs(cumulative[ind] - p)
    return toterr


def fit_distribution_MSGT(options: OptionChain):

    sorted_call_strikes = options.get_call_strikes()
    sorted_put_strikes = options.get_put_strikes()
    options_dict_calls = options.get_calls()
    options_dict_puts = options.get_puts()

    strikes = []
    probs = []
    D = 1
    strikes, probs = add_call_bull_spreads(sorted_call_strikes, options_dict_calls, strikes, probs, D=D)
    strikes, probs = add_put_bull_spreads(sorted_put_strikes, options_dict_puts, strikes, probs, D=D)

    start = [options.underlying, options.underlying / 5, 0]

    tic = time.time()
    res = minimize(fit_MSGT, start, method = 'Nelder-Mead', args=(strikes, probs), options={'maxiter' : 3000})
    toc = time.time()
    logger.info("Optimization MSGT: error {} res {} time {}".format(res.fun, res.x, toc-tic))
    
    return Distribution("MSGT", res.x)


def fit_distribution_LIS(options: OptionChain):
    sorted_call_strikes = options.get_call_strikes()
    sorted_put_strikes = options.get_put_strikes()
    options_dict_calls = options.get_calls()
    options_dict_puts = options.get_puts()

    D = 1
    strikes1, probs1 = add_call_bull_spreads(sorted_call_strikes, options_dict_calls, [], [], D=D)
    strikes2, probs2 = add_put_bull_spreads(sorted_put_strikes, options_dict_puts, [], [], D=D)

    strikes, probs = [], []
    i, j, N, M = 0, 0, len(strikes1), len(strikes2)
    while i < N-1 or j < M-1:
        if i == N or strikes1[i] > strikes2[j]:
            strikes.append(strikes2[j])
            probs.append(probs2[j])
            j += 1
        else:
            strikes.append(strikes1[i])
            probs.append(probs1[i])
            i += 1

    N = len(strikes)
    prev = [i for i in range(N)]
    totl = [0 for i in range(N)]
    lind = 0

    for i in range(N):
        for j in range(i):
            if probs[i] > probs[j]:
                if totl[i] < 1 + totl[j]:
                    totl[i] = 1 + totl[j]
                    prev[i] = j
        if totl[i] >= totl[lind]:
            lind = i

    kept_st, kept_pr = [strikes[lind], 100000], [probs[lind], 1]
    while lind != prev[lind]:
        lind = prev[lind]
        kept_st.append(strikes[lind])
        kept_pr.append(probs[lind])
    kept_st.append(0)
    kept_pr.append(0)

    kept_st.reverse()
    kept_pr.reverse()

    return Distribution('N', [kept_st, kept_pr])


def curve_fit_optim(x, scale, d1, d2):
    bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
    ba = d1 / 2
    bb = d2 / 2
    return betainc(ba, bb, bx)    


def fit_distribution_F(options: OptionChain):
    sorted_call_strikes = options.get_call_strikes()
    sorted_put_strikes = options.get_put_strikes()
    options_dict_calls = options.get_calls()
    options_dict_puts = options.get_puts()

    strikes = []
    probs = []
    D = 2
    strikes, probs = add_call_bull_spreads(sorted_call_strikes, options_dict_calls, strikes, probs, D)
    strikes, probs = add_put_bull_spreads(sorted_put_strikes, options_dict_puts, strikes, probs, D)

    tic = time.time()
    popt, _ = curve_fit(curve_fit_optim, strikes, probs)
    toc = time.time()
    logger.info("Optimization F: res {} time {}".format(popt, toc-tic))

    return Distribution('F', popt)


def expectation_calc(x, *args):
    call_premium, call_strikes, put_premium, put_strikes = args
    distr = Distribution('FF', x)

    interpolated_strikes, prob_array, _ = distr.get_prob_arrays(steps=400)
    toterr = 0
    # Eval all calls
    for st, p in zip(call_strikes, call_premium):
        expected = -p
        for ist, pr in zip(interpolated_strikes, prob_array):
            if ist >= st:
                expected += (ist - st) * pr
        toterr += abs(expected)
    logger.info(x)
    logger.info(toterr)
    return toterr


def fit_distribution_FF(options: OptionChain):
    options_dict_calls = options.get_calls()
    options_dict_puts = options.get_puts()
    
    call_premium = []
    call_strikes = []
    for strike in options_dict_calls.keys():
        premium = options_dict_calls[strike][0].get_premium()
        if premium >= 0.05:
            call_strikes.append(strike)
            call_premium.append(premium)

    put_premium = []
    put_strikes = []
    for strike in options_dict_puts.keys():
        premium = options_dict_puts[strike][0].get_premium()
        if premium >= 0.05:
            put_strikes.append(strike)
            put_premium.append(premium)       

    res = minimize(expectation_calc, [100, 10, 10, 100, 10, 10, 0.5], args=(call_premium, call_strikes, put_premium, put_strikes), options={'maxiter':10})

    return Distribution('FF', sol)
