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

import plotly

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

    ########################################


 



    context = {
        'option_details': enriched_option_details,
        'current_price': current_price,
        'multiplied_current_price': 10 * current_price,
      
    }


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
                        enriched_option_details.append((option_type, detail[1], {'strikes': available_strikes.tolist(), 'last_prices': {k: float(v) for k, v in last_prices.items()}, 'default_strike': float(default_strike), 'default_premium': float(default_premium)}))
                    else:
                        enriched_option_details.append(detail)
                
                ########################################
                # Calculate payoff profile
                def calculate_payoff(price_range, enriched_option_details):
                    total_payoff = np.zeros_like(price_range)
                    for data in enriched_option_details:
                        if data[0] == 'Stock':
                            continue  # Skip stock entries as they do not have a strike or intrinsic value calculation
                        elif data[0] in ['Call', 'Put']:
                            option_type, strike_data = data[0], data[2]
                            strike = strike_data['default_strike']
                            premium = strike_data['default_premium']
                            quantity = 1  # Default quantity for a single option contract
                        else:
                            option_type, strike, premium, quantity = data

                        intrinsic_values = np.maximum(price_range - strike, 0) if option_type == 'Call' else np.maximum(strike - price_range, 0)
                        payoff = premium - intrinsic_values if 'Short' in option_type else intrinsic_values - premium
                        total_payoff += payoff * quantity
                    return total_payoff


                price_range = np.linspace(0.5 * current_price, 1.5 * current_price, 400)
                payoffs = calculate_payoff(price_range, enriched_option_details)

                # Display calculated maximum gain, maximum loss, and breakeven points
                max_gain = max(payoffs)
                max_loss = min(payoffs)

                # Calculate breakeven points
                breakeven_indices = np.where(np.diff(np.sign(payoffs)))[0]  # Get indices where payoffs cross zero
                breakeven_points = price_range[breakeven_indices]
                # Optional: Round breakeven points to reduce precision noise
                breakeven_points = np.round(breakeven_points, 2)
                # Deduplicate and sort breakeven points
                breakeven_points = sorted(set(breakeven_points))
                # Display breakeven points
                breakeven_output = ", ".join(f"${bp:.2f}" for bp in breakeven_points)
                print("breakeven_output", breakeven_output)


                # Plotting the payoff diagram
                fig = go.Figure()

                # Adding the basic payoff trace
                fig.add_trace(go.Scatter(x=price_range, y=payoffs, mode='lines', name='Net Payoff', line=dict(color='blue')))

                # Calculate and round breakeven points
                breakeven_indices = np.where(np.diff(np.sign(payoffs)))[0]  # Get indices where payoffs cross zero
                breakeven_points = price_range[breakeven_indices]
                breakeven_points = np.round(breakeven_points, 2)  # Round breakeven points to reduce precision noise

                # Adding breakeven points as a single trace
                fig.add_trace(go.Scatter(
                        x=breakeven_points,
                        y=[0] * len(breakeven_points),
                        mode='markers',
                        marker=dict(color='red', size=12),
                        name='Breakeven Points'
                    ))

                # Adjust the x-axis range to focus around breakeven points and current stock price
                if breakeven_points.any():
                        buffer = (price_range.max() - price_range.min()) * 0.05  # Smaller buffer
                        fig.update_xaxes(range=[min(breakeven_points) - buffer, max(breakeven_points) + buffer])

                # Set a custom width and height for the graph
                fig.update_layout(
                    xaxis_title="Stock Price at Expiry",
                    yaxis_title="Net Payoff",
                    showlegend=False,  # This disables the legend
                    autosize=False,
                    width=800,
                    height=600
                )

                fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


                # Generate and display the summary content
                summary_content = generate_summary(
                        symbol, current_price, strategy, trade_duration, expiration_date, enriched_option_details
                    )
                st.markdown(summary_content, unsafe_allow_html=True)


                # Format the summary content for display
                formatted_summary = []
                for line in summary_content.splitlines():
                    if line.startswith('Option Leg'):
                        if line.startswith('Option Leg 1'):
                            formatted_summary.append({
                                'option_leg': True,
                                'content': line.replace("Average Share Cost", "Quantity")
                            })
                        else:
                            formatted_summary.append({
                                'option_leg': True,
                                'content': line
                            })
                    elif line.startswith('Type: Call'):
                        formatted_summary.append({
                            'indent': True,
                            'content': line + " Quantity: 1"
                        })
                    else:
                        formatted_summary.append({
                            'content': line
                        })
                

                # Generate the Yahoo Finance options page URL for the entered symbol
                yahoo_finance_url = f"https://finance.yahoo.com/quote/{symbol}/options"


                return JsonResponse({
                    'expiration_dates': expiration_dates,
                    'current_price': current_price,
                    'calls_data': calls_data_dict,
                    'puts_data': puts_data_dict,
                    'enriched_option_details': enriched_option_details,
                    'max_gain': max_gain,
                    'max_loss': max_loss,
                    'breakeven_output': breakeven_output,
                    'fig_json': fig_json,  
                    'formatted_summary': formatted_summary, 
                    'yahoo_finance_url': yahoo_finance_url,  
                    'symbol': symbol,
            
                    'shares': shares,  
                    'share_cost': share_cost,  
                    'selected_strike': selected_strike,  
                    'selected_premium': selected_premium,  
                    'selected_quantity': selected_quantity,  
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
    return redirect('login')

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