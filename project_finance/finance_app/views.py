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

def front_page_view(request):
    context = {}
    context['page_title'] = 'Comprehensive Options Strategy Analyzer'

    # User input for ticker symbol
    st.sidebar.subheader('Options Strategy Analyzer')

    # User input for ticker symbol
    symbol = st.sidebar.text_input('Enter Ticker Symbol', 'SPY', key='ticker_input')
    ticker = yf.Ticker(symbol)

    # Fetch real-time data
    try:
        current_price = ticker.history(period='1d')['Close'].iloc[-1]
        st.sidebar.write(f"Current price of {symbol}: ${current_price:.2f}")
    except IndexError:
        st.sidebar.error("Failed to retrieve stock data. Check the ticker symbol and try again.")
        st.stop()

    # Sidebar for defining option strategy
    strategy = st.sidebar.selectbox('Choose Strategy', ['Covered Call', 'Collar', 'Put Sale'], key='strategy_select')

    # Add trade duration choice
    trade_duration = st.sidebar.selectbox("How long would you like to implement this trade?",
                                        ["Less than 30 days", "30-90 days", "90+ days"], key='trade_duration_select')

    # Fetch and display options chains using the refactored function
    exps, all_options = options_chain(symbol)
    today = pd.Timestamp.now().normalize()

    # Filter options based on the selected trade duration
    if trade_duration == "Less than 30 days":
        all_options = all_options[pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=30)]
    elif trade_duration == "30-90 days":
        all_options = all_options[(today + pd.DateOffset(days=30) < pd.to_datetime(all_options['Expiration Date'])) & (pd.to_datetime(all_options['Expiration Date']) <= today + pd.DateOffset(days=90))]
    else:  # "90+ days"
        all_options = all_options[pd.to_datetime(all_options['Expiration Date']) > today + pd.DateOffset(days=90)]

    if all_options.empty:
        st.sidebar.write("No options data available for the selected duration.")
        st.stop()


    # Filtering the options for selected expiration date and then separating Calls and Puts
    selected_date = st.sidebar.selectbox('Select Expiry Date:', pd.unique(all_options['Expiration Date']), key='expiry_date_select')
    selected_options = all_options[all_options['Expiration Date'] == selected_date]

    # Explicitly filter for Calls and Puts based on a pattern in the contract name
    selected_calls = selected_options[selected_options['Contract Name'].apply(lambda x: re.search(r'[CP]\d+$', x) and 'C' in x)]
    selected_puts = selected_options[selected_options['Contract Name'].apply(lambda x: re.search(r'[CP]\d+$', x) and 'P' in x)]


    # Display Calls panel at the top with a scrollable area
    st.subheader('Calls')
    st.dataframe(selected_calls, height=275)  # Adjust the height as needed

    # Display Puts panel below, also with a scrollable area
    st.subheader('Puts')
    st.dataframe(selected_puts, height=275)  # Adjust the height as needed

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

    # Fetch the details specific to the selected strategy
    option_details = strategy_details[strategy]




    # Enrich option details with strike prices and premiums
    enriched_option_details = []
    for detail in option_details:
        option_type = detail[0]
        if option_type in ['Call', 'Put']:
            if option_type == 'Call':
                available_strikes = selected_calls['Strike'].unique()
                last_prices = {strike: selected_calls[selected_calls['Strike'] == strike]['Last Price'].iloc[0] for strike in available_strikes}
            else:
                available_strikes = selected_puts['Strike'].unique()
                last_prices = {strike: selected_puts[selected_puts['Strike'] == strike]['Last Price'].iloc[0] for strike in available_strikes}
            default_strike = available_strikes[0]
            default_premium = last_prices[default_strike]
            enriched_option_details.append((option_type, detail[1], {'strikes': available_strikes, 'last_prices': last_prices, 'default_strike': default_strike, 'default_premium': default_premium}))
        else:
            enriched_option_details.append(detail)

    print("option_type:", option_type)






    context = {
        'option_details': enriched_option_details,
        'current_price': current_price,
        'multiplied_current_price': 10 * current_price
    }



    # Debugging output
    print("Enriched option details:", enriched_option_details)
    print("Current price:", current_price)

    return render(request, 'finance_app/frontpage.html', context)



        

def process_all_inputs(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        symbol = request.GET.get('symbol')
        strategy = request.GET.get('strategy')
        trade_duration = request.GET.get('trade_duration')
        expiration_date = request.GET.get('expiration_date')
        shares = request.GET.get('shares')
        share_cost = request.GET.get('share_cost')
        selected_strike = request.GET.get('strike')
        selected_premium = request.GET.get('premium')
        selected_quantity = request.GET.get('quantity')
        print("Shares:", shares)
        print("Share Cost:", share_cost)
        print("Strike:", selected_strike)
        print("Premium:", selected_premium)
        print("Quantity:", selected_quantity)

        
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

                                    # Dynamically generate inputs based on strategy selection
                for i, (option_type, *labels) in enumerate(option_details):
                   

                        if option_type == 'Stock':
                            number_of_shares = shares
                            average_share_cost = share_cost
                            options_data.append((option_type, number_of_shares, average_share_cost))
                        else:
                            available_strikes = selected_calls['Strike'].unique() if option_type == 'Call' else selected_puts['Strike'].unique()
                            strike = selected_strike

                            # Retrieve the last price for the selected strike price
                            if strike:
                                option_data = selected_calls if option_type == 'Call' else selected_puts
                                last_price = option_data[option_data['Strike'] == strike]['Last Price'].iloc[0] if not option_data[option_data['Strike'] == strike].empty else 0.0

                                premium = selected_premium
                                quantity = selected_quantity
                                options_data.append((option_type, strike, premium, quantity))

    
                

                
                return JsonResponse({
                    'expiration_dates': expiration_dates,
                    'current_price': current_price,
                    'calls_data': calls_data_dict,
                    'puts_data': puts_data_dict,
                    'option_details': option_details,
                    'options_data': options_data,
                })
               
                
            else:
                print("No specific expiration date selected, returning expiration dates")
                return JsonResponse({'expiration_dates': expiration_dates})

        except Exception as e:
            print(f"Error during data fetching: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    







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