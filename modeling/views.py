from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template import RequestContext

import json
import logging

from .options_expiry_scraper import scrape_option_dates, scrape_option_expiries
from .options_price_scraper import scrape_option_prices
from .optimization import fit_distribution_F
from .distribution import Distribution
from .options import Option

logger = logging.getLogger(__name__)

STEPS = 22
#DISTRIB = 'MSGT'
DISTRIB = 'F'

def option_from_array(type, arr):
    if type == 'CALL':
        return Option(type='CALL', bid=arr[2], ask=arr[3], strike=arr[0])
    if type == 'PUT':
        return Option(type='PUT', bid=arr[2], ask=arr[3], strike=arr[0])
    return None
    

def format_float(val):
    return "{:.2f}".format(val)


def calculate_portfolio_details(distr_modded, callqty, putqty, callchain, putchain, special):
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
    for i in range(len(interpolated_strikes)):
        if mark == len(strike_list):
            break
        if interpolated_strikes[i] >= strike_list[mark]:
            strike_returns.append({'x': strike_list[mark],
                                   'e': format_float(portfolio_returns[i]),
                                   'pe': portfolio_returns[i] * prob_array[i]})
            mark += 1
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
    if mean_level == 0 and var_level == 0:
        special = True

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
    return JsonResponse(response)


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
    if mean_level == 0 and var_level == 0:
        special = True

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

    return JsonResponse(response)


def modeling(request):
    modeling_context = {}
    if request.method == 'POST':
        # User picked a ticker
        if 'submit_ticker' in request.POST:
            ticker = request.POST.get('new_ticker').upper()

            # Get available expiry dates
            date_list, ticker_type = scrape_option_dates(ticker, 'stock')
            modeling_context['ticker_type'] = ticker_type
            if len(date_list) == 0:
                modeling_context['bad_ticker'] = ticker
            modeling_context['ticker'] = ticker
            modeling_context['dates'] = date_list

        # User picked a date
        elif 'new_date' in request.POST:
            date_str = request.POST.get('new_date')
            ticker = request.POST.get('ticker')
            ticker_type = request.POST.get('ticker_type')

            modeling_context['date_picked'] = date_str
            modeling_context['ticker'] = ticker
            modeling_context['ticker_type'] = ticker_type
            modeling_context['dates'] = request.POST.getlist('date_array')

            # Get expiry dates
            month, year = date_str.split(' ')            
            expiries = scrape_option_expiries(ticker, month, year, ticker_type)
            modeling_context['expiries'] = expiries

        # User picked an expiry
        elif 'new_expiry' in request.POST:
            date_str = request.POST.get('date_picked')
            ticker = request.POST.get('ticker')
            ticker_type = request.POST.get('ticker_type')
            expiry_picked = request.POST.get('new_expiry')
        
            modeling_context['date_picked'] = date_str
            modeling_context['ticker'] = ticker
            modeling_context['ticker_type'] = ticker_type
            modeling_context['dates'] = request.POST.getlist('date_array')
            modeling_context['expiries'] = request.POST.getlist('expiry_array')
            modeling_context['expiry_picked'] = expiry_picked

            # Get option chain data
            month, year = date_str.split(' ')
            options_chain = scrape_option_prices(ticker, month, year, expiry_picked, ticker_type)
            call_table = options_chain.get_call_table()
            put_table = options_chain.get_put_table()            

            # Fit distribution
            distr = fit_distribution_F(options_chain)
            distr.adjust_min_strike()
            distr.adjust_max_strike()
            update_option_expectations(distr, call_table, put_table, special=True)

            modeling_context['call_chain'] = call_table
            modeling_context['put_chain'] = put_table
            modeling_context['chart'] = json.dumps(distr.to_dict_array(steps=STEPS))
            modeling_context['distrib_params'] = distr.params
            modeling_context['mean_level'] = 0
            modeling_context['var_level'] = 0
    
    # Always render the same page
    return render(request, 'modeling.html', modeling_context)
