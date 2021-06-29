from django.core.cache import cache
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect

import datetime
import json
import logging
import pytz
import time

from .options_expiry_scraper import scrape_all_expiries
from .options_price_scraper import scrape_option_prices
from .optimization import fit_distribution_F
from .distribution import Distribution
from .options import Option

logger = logging.getLogger(__name__)

STEPS = 42
#DISTRIB = 'MSGT'
DISTRIB = 'F'

month_map = {'Jan' : 'January', 'Feb' : 'February', 'Mar' : 'March',\
                 'Apr' : 'April', 'May' : 'May', 'Jun' : 'June', \
                 'Jul' : 'July', 'Aug' : 'August', 'Sep' : 'September', \
                 'Oct' : 'October', 'Nov' : 'November', 'Dec' : 'December',
}

def decode_expiry(expiry):
    month_day, year = expiry.split(',')
    year = year.strip()
    month, day = month_day.split(' ')
    month = month_map[month]
    return day, month, year


def get_date_time():
    dto = datetime.datetime.utcnow()
    dto=dto.replace(tzinfo=pytz.UTC)
    dto_nyse=dto.astimezone(pytz.timezone("America/New_York"))
    return dto_nyse.strftime("%d/%m/%Y %H:%M:%S")


def option_from_array(type, arr):
    if type == 'CALL':
        return Option(type='CALL', bid=arr[2], ask=arr[3], strike=arr[0])
    if type == 'PUT':
        return Option(type='PUT', bid=arr[2], ask=arr[3], strike=arr[0])
    return None
    

def format_float(val):
    return "{:.2f}".format(val)


def calculate_portfolio_details(distr_modded, callqty, putqty, callchain, putchain, special):
    # Check if portfolio is empty
    if min(callqty) == '0' and max(callqty) == '0' and min(putqty) == '0' and max(putqty) == '0':
        return [], [], [], [], 0, 0, format_float(0.0)

    #Get all the strikes together
    strike_list = set()
    for i in range(len(callchain)):
        strike_list.add(callchain[i][0])
    for i in range(len(callchain)):
        strike_list.add(callchain[i][0])
    strike_list = list(strike_list)
    strike_list.sort()
    strike_min = max(0, strike_list[0] * 0.95)
    strike_max = strike_list[-1] * 1.05
    
    # Refresh portfolio data
    interpolated_strikes, prob_array, _ = distr_modded.get_prob_arrays(th_lower=0.01, 
                                          th_upper=0.01, strike_min=strike_min, strike_max=strike_max)
    portfolio_returns =[0 for i in range(len(interpolated_strikes))]
    portfolio_label = []
    portfolio_qty = []
    totcost = 0
    for i in range(len(callqty)):
        qty = int(callqty[i])
        if qty != 0:
            o = option_from_array('CALL', callchain[i])
            portfolio_label.append(o.summary())
            portfolio_qty.append(qty)

            exp, sharpe, option_payout = o.evaluate(interpolated_strikes, prob_array, special=special)
            for j in range(len(interpolated_strikes)):
                portfolio_returns[j] += qty * option_payout[j]
            totcost += qty * o.get_premium()

    for i in range(len(putqty)):
        qty = int(putqty[i])
        if qty != 0:
            o = option_from_array('PUT', putchain[i])
            portfolio_label.append(o.summary())
            portfolio_qty.append(qty)

            exp, sharpe, option_payout = o.evaluate(interpolated_strikes, prob_array, special=special)
            for j in range(len(interpolated_strikes)):
                portfolio_returns[j] += qty * option_payout[j]
            totcost += qty * o.get_premium()

    # Get plottable returns chart
    chart = []
    minind = 0
    maxind = len(interpolated_strikes) - 1
    while interpolated_strikes[minind] < strike_min:
        minind += 1
    while interpolated_strikes[maxind] > strike_max:
        maxind -= 1

    for i in range(minind, maxind + 1):
        chart.append({'x' : interpolated_strikes[i],
                      'e' : portfolio_returns[i],
                      'pe' : portfolio_returns[i] * prob_array[i],
                      'p' : str(format_float(prob_array[i] * 100))+"%"})

    # Interpolate strike returns
    mark = 0
    strike_returns = []
    i = 0
    while i <len(interpolated_strikes):
        if mark == len(strike_list):
            break
        if interpolated_strikes[i] >= strike_list[mark]:
            strike_returns.append({'x': strike_list[mark],
                                   'e': format_float(portfolio_returns[i]),
                                   'pe': portfolio_returns[i] * prob_array[i]})
            mark += 1
            i -= 1
        i += 1

    expr = 0
    winp = 0
    for r, p in zip(portfolio_returns, prob_array):
        if r >= 0:
            winp += p
        expr += p*r
    winp /= sum(prob_array)
    expr /= sum(prob_array)
    winp = format_float(winp * 100)
    expr = format_float(expr)
    
    return chart, strike_returns, portfolio_label, portfolio_qty, expr, winp, format_float(totcost*100)


def update_option_expectations(distr_modded, callchain, putchain, special):
    #Update expectations for options
    strikes, prob_array, _ = distr_modded.get_prob_arrays(th_lower=0.001, th_upper=0.001)
    for arr in callchain:
        o = option_from_array('CALL', arr)
        exp, sharpe, r = o.evaluate(strikes, prob_array, special=special)
        arr[6], arr[7] = exp / (o.get_premium()), sharpe

    for arr in putchain:
        o = option_from_array('PUT', arr)
        exp, sharpe, _ = o.evaluate(strikes, prob_array, special=special)
        arr[6], arr[7] = exp / (o.get_premium()), sharpe


def sync(request):
    """
    Synchronize option chain, portfolio, charts, expectations
    """
    mean_level = int(request.POST.get('mean_level'))
    var_level = int(request.POST.get('var_level'))
    callqty = request.POST.getlist('callqty[]')
    putqty = request.POST.getlist('putqty[]')
    ticker = request.POST.get('ticker')
    expiry = request.POST.get('expiry')
    
    day, month, year = decode_expiry(expiry)

    # Refresh option table
    options_chain = scrape_option_prices(ticker, month, year, expiry)
    callchain = options_chain.get_call_table()
    putchain = options_chain.get_put_table()
    
    # Fit distribution
    distr = fit_distribution_F(options_chain)
    distr.adjust_min_strike()
    distr.adjust_max_strike()
    distrib_params = distr.params

    # Fit modded distribution
    distr_modded = Distribution(DISTRIB, distrib_params)
    distr_modded.set_mean_shift_level(mean_level)
    distr_modded.set_var_shift_level(var_level)
    distr_modded.adjust_min_strike()
    distr_modded.adjust_max_strike()

    # Take min/max over both
    minv = min(distr.min_strike, distr_modded.min_strike)
    maxv = max(distr.max_strike, distr_modded.max_strike)            
    distr.min_strike, distr_modded.min_strike = minv, minv
    distr.max_strike, distr_modded.max_strike = maxv, maxv

    # Handle RND
    special = False
    #if mean_level == 0 and var_level == 0:
    #    special = True

    #Update expectations for options
    update_option_expectations(distr_modded, callchain, putchain, special=special)

    # Get portfolio updates
    portfoliochart, strike_returns, portfolio_label, portfolio_qty, expr, winp, totcost = calculate_portfolio_details(distr_modded, callqty, putqty, callchain, putchain, special)

    response = {
        "price" : options_chain.underlying,
        "callchain" : callchain,
        "putchain" : putchain,
        "chart" : distr.to_dict_array(steps=STEPS),
        "chart_modded" : distr_modded.to_dict_array(steps=STEPS),
        "portfoliochart" : portfoliochart,
        "strikes" : strike_returns,
        "portfolio_label" : portfolio_label,
        "portfolio_qty" : portfolio_qty,
        "expr" : expr,
        "winp" : winp,
        "totcost" : totcost,
        "distrib_params" : distrib_params,
        "datetime" : get_date_time()
    }

    # Logging
    logger.info("Sync! Ticker: {} Expiry: {} Mean: {} Var: {} PfLabel: {} PfQty: {}".format(ticker, expiry, mean_level, var_level, portfolio_label, portfolio_qty))

    return JsonResponse(response)


def update_portfolio(request):
    distrib_params = request.POST.getlist('distrib_params[]')
    callchain = json.loads(request.POST.get('callchain'))
    putchain = json.loads(request.POST.get('putchain'))
    mean_level = int(request.POST.get('mean_level'))
    var_level = int(request.POST.get('var_level'))
    callqty = request.POST.getlist('callqty[]')
    putqty = request.POST.getlist('putqty[]')
    
    # Fit modded distribution
    distr_modded = Distribution(DISTRIB, distrib_params)
    distr_modded.set_mean_shift_level(mean_level)
    distr_modded.set_var_shift_level(var_level)
    distr_modded.adjust_min_strike()
    distr_modded.adjust_max_strike()

    # Handle RND
    special = False
    #if mean_level == 0 and var_level == 0:
    #    special = True

    # Get portfolio updates
    portfoliochart, strike_returns, portfolio_label, portfolio_qty, expr, winp, totcost = calculate_portfolio_details(distr_modded, callqty, putqty, callchain, putchain, special)
    response = {
        "portfoliochart" : portfoliochart,
        "strikes" : strike_returns,
        "portfolio_label" : portfolio_label,
        "portfolio_qty" : portfolio_qty,
        "expr" : expr,
        "winp" : winp,
        "totcost" : totcost
    }

    # Logging
    ticker = request.POST.get('ticker')
    expiry = request.POST.get('expiry')
    logger.info("Ticker: {} Expiry: {} Mean: {} Var: {} PfLabel: {} PfQty: {}".format(ticker, expiry, mean_level, var_level, portfolio_label, portfolio_qty))

    return JsonResponse(response)


def update_chart(request):
    distrib_params = request.POST.getlist('distrib_params[]')
    callchain = json.loads(request.POST.get('callchain'))
    putchain = json.loads(request.POST.get('putchain'))
    mean_level = int(request.POST.get('mean_level'))
    var_level = int(request.POST.get('var_level'))
    callqty = request.POST.getlist('callqty[]')
    putqty = request.POST.getlist('putqty[]')

    # Fit modded distribution
    distr = Distribution(DISTRIB, distrib_params)
    distr.adjust_min_strike()
    distr.adjust_max_strike()

    distr_modded = Distribution(DISTRIB, distrib_params)
    distr_modded.set_mean_shift_level(mean_level)
    distr_modded.set_var_shift_level(var_level)
    distr_modded.adjust_min_strike()
    distr_modded.adjust_max_strike()

    # Take min/max over both
    minv = min(distr.min_strike, distr_modded.min_strike)
    maxv = max(distr.max_strike, distr_modded.max_strike)            
    distr.min_strike, distr_modded.min_strike = minv, minv
    distr.max_strike, distr_modded.max_strike = maxv, maxv

    # Handle RND
    special = False
    #if mean_level == 0 and var_level == 0:
    #    special = True

    #Update expectations for options
    update_option_expectations(distr_modded, callchain, putchain, special=special)

    response = {
        "chart" : distr.to_dict_array(steps=STEPS),
        "chart_modded" : distr_modded.to_dict_array(steps=STEPS),
        "callchain" : callchain,
        "putchain" : putchain
    }

    # Get portfolio updates
    portfoliochart, strike_returns, portfolio_label, portfolio_qty, expr, winp, totcost = calculate_portfolio_details(distr_modded, callqty, putqty, callchain, putchain, special)

    response["portfoliochart"] = portfoliochart
    response["strikes"] = strike_returns
    response["portfolio_label"] = portfolio_label
    response["portfolio_qty"] = portfolio_qty
    response["expr"] = expr
    response["winp"] = winp
    response["totcost"] = totcost

    # Logging
    ticker = request.POST.get('ticker')
    expiry = request.POST.get('expiry')
    logger.info("Ticker: {} Expiry: {} Mean: {} Var: {} PfLabel: {} PfQty: {}".format(ticker, expiry, mean_level, var_level, portfolio_label, portfolio_qty))

    return JsonResponse(response)

def modeling(request):
    # Default page view!
    modeling_context = {}
    ticker = 'SPY'

    if request.method == 'POST':
        # User picked a ticker
        if 'new_ticker' in request.POST:
            ticker = request.POST.get('new_ticker').upper()

        if 'submit_ticker' in request.POST:
            logger.info("Picked NEW Ticker {}".format(ticker))

        if 'new_exp' in request.POST:
            expiry_picked = request.POST.get('new_exp')
            date_list, date_picked, _ = cache.get_or_set(ticker, lambda: scrape_all_expiries(ticker), timeout=60*60)
            if len(date_list) == 0:
                modeling_context['bad_ticker'] = ticker
            else:
                modeling_context['expiries'] = date_list
                modeling_context['date_picked'] = date_picked
                modeling_context['expiry_picked'] = expiry_picked
            logger.info("Picked NEW Expiry {}".format(expiry_picked))
    
    if 'expiry_picked' not in modeling_context:
        if len(ticker) == 0:
            modeling_context['empty_ticker'] = True
        else:
            date_list, date_picked, expiry_picked = cache.get_or_set(ticker, lambda: scrape_all_expiries(ticker), timeout=60*60)
            if len(date_list) == 0:
                modeling_context['bad_ticker'] = ticker
            else:
                modeling_context['expiries'] = date_list
                modeling_context['date_picked'] = date_picked
                modeling_context['expiry_picked'] = expiry_picked

    if 'call_chain' not in modeling_context:
        if 'expiry_picked' in modeling_context:
            # Get option chain data
            expiry_picked = modeling_context['expiry_picked']
            day, month, year = decode_expiry(expiry_picked)
            options_chain = scrape_option_prices(ticker, month, year, expiry_picked)
            call_table = options_chain.get_call_table()
            put_table = options_chain.get_put_table()

            # Fit distribution
            distr = fit_distribution_F(options_chain)
            distr.adjust_min_strike()
            distr.adjust_max_strike()
            update_option_expectations(distr, call_table, put_table, special=True)

            modeling_context['price'] = options_chain.underlying
            modeling_context['call_chain'] = call_table
            modeling_context['put_chain'] = put_table
            modeling_context['chart'] = json.dumps(distr.to_dict_array(steps=STEPS))
            modeling_context['distrib_params'] = distr.params
            modeling_context['mean_level'] = 0
            modeling_context['var_level'] = 0
            modeling_context['datetime'] = get_date_time()

    # Fill in context info for first rendering
    modeling_context['ticker'] = ticker

    # Always render the same page
    return render(request, 'modeling.html', modeling_context)


def redir(request):
    return HttpResponseRedirect('modeling')
