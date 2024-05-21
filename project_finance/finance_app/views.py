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

import json

# view of the landing page
def front_page_view(request):
    context = {}
    context['page_title'] = 'Comprehensive Options Strategy Analyzer'

    return render(request, 'finance_app/frontpage.html', context)


        

def process_all_inputs(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        symbol = request.GET.get('symbol')
        strategy = request.GET.get('strategy')
        trade_duration = request.GET.get('trade_duration')
        expiration_date = request.GET.get('expiration_date')
        number_of_shares = request.GET.get('shares')
        average_share_cost = request.GET.get('share_cost')
        print("no of shares:", number_of_shares)
        print("Average share cost:", average_share_cost)

        
        print(f"Received parameters: symbol={symbol}, strategy={strategy}, trade_duration={trade_duration}, expiration_date={expiration_date}")

        if not symbol or not trade_duration:
            return JsonResponse({'error': 'No symbol or trade duration provided'}, status=400)

        try:
            exps, all_options = options_chain(symbol)
            today = pd.Timestamp.now().normalize()


            if trade_duration == "Less than 30 days":
                all_options = all_options[pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=30)]
                print("Filtered options for Less than 30 days")
            elif trade_duration == "30-90 days":
                all_options = all_options[(today + pd.DateOffset(days=30) < pd.to_datetime(all_options['Expiration Date'])) & (pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=90))]
                print("Filtered options for 30-90 days")
            else:  # "90+ days"
                all_options = all_options[pd.to_datetime(all_options['Expiration Date']) > today + pd.DateOffset(days=90)]
                print("Filtered options for 90+ days")

            if all_options.empty:
                return JsonResponse({'error': 'No options data available for the selected duration.'}, status=400)

            expiration_dates = all_options['Expiration Date'].unique().tolist()


            if expiration_date:
                selected_options = all_options[all_options['Expiration Date'] == expiration_date]

                selected_calls = selected_options[selected_options['Contract Name'].apply(lambda x: re.search(r'[CP]\d+$', x) and 'C' in x)]
                selected_puts = selected_options[selected_options['Contract Name'].apply(lambda x: re.search(r'[CP]\d+$', x) and 'P' in x)]

                 # Replace NaN and inf values
                calls_data = selected_calls.replace([np.inf, -np.inf], np.nan).fillna(0)

                calls_data_dict = calls_data.to_dict(orient='records')

                 # Replace NaN and inf values
                puts_data = selected_puts.replace([np.inf, -np.inf], np.nan).fillna(0)

                puts_data_dict = puts_data.to_dict(orient='records')



                current_price = yf.Ticker(symbol).history(period='1d')['Close'].iloc[-1]
                print(f"Current price: {current_price}")

                options_data = []
                # Determine the number of option legs based on the strategy
                if strategy == 'Covered Call':
                    option_types = ['Call', 'Stock']
                elif strategy == 'Collar':
                    option_types = ['Stock', 'Put', 'Call']
                elif strategy == 'Put Sale':
                    option_types = ['Put']

                # Define the dynamic labeling and inputs based on the strategy
                strategy_details = {
                    'Covered Call': [('Stock', 'Number of Shares', 'Average Share Cost'), ('Call', 'Call Strike Price')],
                    'Collar': [('Stock', 'Number of Shares', 'Average Share Cost'), ('Put', 'Put Strike Price'),
                            ('Call', 'Call Strike Price')],
                    'Put Sale': [('Put', 'Put Strike Price')]
                }



                option_details = strategy_details[strategy]



                option_last_prices = []
                for i, (option_type, *labels) in enumerate(option_details):
                    if option_type in ['Call', 'Put']:
                        option_data = selected_calls if option_type == 'Call' else selected_puts
                        available_strikes = option_data['Strike'].unique()
                        last_price_data = {strike: option_data[option_data['Strike'] == strike]['Last Price'].iloc[0] if not option_data[option_data['Strike'] == strike].empty else 0.0 for strike in available_strikes}
                        option_last_prices.append(last_price_data)
                    else:
                        option_last_prices.append(None)

               
                return JsonResponse({
                    'expiration_dates': expiration_dates,
                    'current_price': current_price,
                    'calls_data': calls_data_dict,
                    'puts_data': puts_data_dict,
                    'option_details': option_details,
                    'option_last_prices': option_last_prices,
                })
            else:
                print("No specific expiration date selected, returning expiration dates")
                return JsonResponse({'expiration_dates': expiration_dates})

        except Exception as e:
            print(f"Error during data fetching: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    print("Invalid request")
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