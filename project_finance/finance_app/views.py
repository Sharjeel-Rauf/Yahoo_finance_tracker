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

   


   
    return render(request, 'finance_app/frontpage.html', context)


def process_all_inputs(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        symbol = request.GET.get('symbol')
        strategy = request.GET.get('strategy')
        print("strategy", strategy)
        trade_duration = request.GET.get('trade_duration')
        expiration_date = request.GET.get('expiration_date')
        print(trade_duration)

        if not symbol or not trade_duration:
            return JsonResponse({'error': 'No symbol or trade duration provided'}, status=400)

        try:
            exps, all_options = options_chain(symbol)
            today = pd.Timestamp.now().normalize()

            print("hello1")

            if trade_duration == "Less than 30 days":
                all_options = all_options[pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=30)]
                print("hello2")
            elif trade_duration == "30-90 days":
                all_options = all_options[(today + pd.DateOffset(days=30) < pd.to_datetime(all_options['Expiration Date'])) & (pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=90))]
            else:  # "90+ days"
                all_options = all_options[pd.to_datetime(all_options['Expiration Date']) > today + pd.DateOffset(days=90)]

            if all_options.empty:
                return JsonResponse({'error': 'No options data available for the selected duration.'}, status=400)

            
            expiration_dates = all_options['Expiration Date'].unique().tolist()
            

            if expiration_date:
                selected_options = all_options[all_options['Expiration Date'] == expiration_date]

                selected_calls = selected_options[selected_options['Contract Name'].apply(lambda x: re.search(r'[CP]\d+$', x) and 'C' in x)]
                selected_puts = selected_options[selected_options['Contract Name'].apply(lambda x: re.search(r'[CP]\d+$', x) and 'P' in x)]

                calls_data = selected_calls.to_dict(orient='records')
                puts_data = selected_puts.to_dict(orient='records')

                current_price = yf.Ticker(symbol).history(period='1d')['Close'].iloc[-1]

                options_data = []
                # Determine the number of option legs based on the strategy
                if strategy == 'Covered Call':
                    option_types = ['Call', 'Stock']
                    print(option_types)
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

                # Fetch the details specific to the selected strategy
                option_details = strategy_details[strategy]

                # Clear previous inputs to avoid duplication
                for key in st.session_state.keys():
                    if 'shares_' in key or 'premium_' in key or 'quantity_' in key or 'share_cost_' in key or 'Strike_' in key:
                        del st.session_state[key]

                # Dynamically generate inputs based on strategy selection
                for i, (option_type, *labels) in enumerate(option_details):
                    st.sidebar.subheader(f"Option Leg {i + 1}")
            

                return JsonResponse({
                    'expiration_dates': expiration_dates,
                    'current_price': current_price,
                    'calls_data': calls_data,
                    'puts_data': puts_data,
                    'option_details': option_details,
                })
            else:
                return JsonResponse({'expiration_dates': expiration_dates})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

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