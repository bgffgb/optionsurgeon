from django.shortcuts import render, redirect
from django.template import RequestContext
import logging

from .options_expiry_scraper import scrape_option_dates, scrape_option_expiries
from .options_price_scraper import scrape_option_prices

logger = logging.getLogger(__name__)


def modeling(request):
    modeling_context = {}
    if request.method == 'POST':
        logger.info(request.POST)

        # User picked a ticker
        if 'new_ticker' in request.POST:
            ticker = request.POST.get('new_ticker').upper()

            # Get available expiry dates
            date_list = scrape_option_dates(ticker, 'stock')
            modeling_context['ticker_type'] = 'stock'
            if len(date_list) == 0:
                date_list = scrape_option_dates(ticker, 'fund')
                modeling_context['ticker_type'] = 'fund'
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

        # User picked a date
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
            table = options_chain.get_table()
            modeling_context['chain'] = table
    
    # Always render the same page
    return render(request, 'modeling.html', modeling_context)
