from django.shortcuts import render, redirect

from django.contrib.auth import login, logout

from .forms import *

from .forms import TickerSymbolForm

import yfinance as yf

import streamlit as st

import numpy as np

import pandas as pd

import plotly.graph_objects as go

import re

from .utils import options_chain, generate_summary

from django.http import JsonResponse

# view of the landing page
def front_page_view(request):
    context = {}
    context['page_title'] = 'Comprehensive Options Strategy Analyzer'

    # Initialize the form with default values or process form submission
    if request.method == 'POST':
        form_symbol = TickerSymbolForm(request.POST)
        if form_symbol.is_valid():
            symbol = form_symbol.cleaned_data['ticker_symbol']
            # Process the ticker data as needed
            # For example, you can pass it to the template for display
    else:
        form_symbol = TickerSymbolForm(initial={'ticker_symbol': 'SPY'})  # Set initial value here

    # Add form to the context
    context['form_symbol'] = form_symbol

    # Fetching the current price of the ticker symbol
    try:
        symbol = 'SPY'  # Default symbol
        ticker = yf.Ticker(symbol)
        current_price = ticker.history(period='1d')['Close'].iloc[-1]

        context.update({
            'symbol': symbol,
            'current_price': current_price,
        })
    except IndexError:
        context['error_message'] = "Failed to retrieve stock data. Check the ticker symbol and try again."
    
    # choosing strategy


    if request.method == 'POST':
        form_strategy = StrategyForm(request.POST)
        if form_strategy.is_valid():
            strategy = form_symbol.cleaned_data['strategy']
            # Process the selected strategy as needed
    else:
        form_strategy = StrategyForm()

    context['form_strategy'] = form_strategy

    # Initialize the form with default values or process form submission
    if request.method == 'POST':
        form_duration = TradeDurationForm(request.POST)
        if form_duration.is_valid():
            duration = form_duration.cleaned_data['trade_duration']
            # Fetch and display options chains using the refactored function
            symbol = 'SPY'  # Default symbol
            exps, all_options = options_chain(symbol)
            today = pd.Timestamp.now().normalize()
            
            # Filter options based on the selected trade duration
            if duration == "Less than 30 days":
                all_options = all_options[pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=30)]
            elif duration == "30-90 days":
                all_options = all_options[(today + pd.DateOffset(days=30) < pd.to_datetime(all_options['Expiration Date'])) & (pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=90))]
            else:  # "90+ days"
                all_options = all_options[pd.to_datetime(all_options['Expiration Date']) > today + pd.DateOffset(days=90)]

            if all_options.empty:
                context['error_message'] = "No options data available for the selected duration."
            else:
                context['all_options'] = all_options
    else:
        form_duration = TradeDurationForm()

    context['form_duration'] = form_duration



   
    return render(request, 'finance_app/frontpage.html', context)



def process_ticker_symbol(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        symbol = request.GET.get('symbol')
        if symbol:
            try:
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
                return JsonResponse({'current_price': current_price})  # Return results as JSON
            except IndexError:
                return JsonResponse({'error': 'Failed to retrieve stock data. Check the ticker symbol and try again.'}, status=400)
        else:
            return JsonResponse({'error': 'No ticker symbol provided'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)








# logout view
def LogoutView(request):
    logout(request)
    return redirect('frontpage')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect('frontpage')
    else:
        form = SignUpForm()
    
    return render(request, 'finance_app/signup.html', {'form': form})