#  streamlit run yf_st6.py --server.port 8503

# 5-3-24
# 5-10-24


import streamlit as st
import numpy as np
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import re




st.set_page_config(page_title='Comprehensive Options Strategy Analyzer', layout='wide')


desired_width = 320
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.float_format = "{:,.2f}".format


def generate_summary(symbol, current_price, strategy, trade_duration, selected_date, options_data):
    summary_lines = [
        f"Ticker Symbol: {symbol}",
        f"Current Price: ${current_price:.2f}",
        f"Strategy: {strategy}",
        f"Trade Duration: {trade_duration}",
        f"Selected Expiry Date: {selected_date}"
    ]

    # Add detailed information about each option leg
    for index, data in enumerate(options_data, start=1):
        if data[0] == 'Stock':
            try:
                shares = 100  # Get the value of shares
                summary_lines.append(
                    f"Option Leg {index}:\n"
                    f"    Type: Stock\n"
                    f"    Shares: {shares}\n"  # Use the actual value of shares
                    f"    Average Share Cost: ${current_price:.2f}\n"
                )
            except (IndexError, ValueError) as e:
                summary_lines.append(f"**Option Leg {index}**: Error processing Stock data: {e}")
        elif data[0] == 'Call':
            try:
                strike_prices = data[2]['strikes']
                last_prices = data[2]['last_prices']
                default_strike = data[2]['default_strike']
                default_premium = data[2]['default_premium']
                quantity = data[2].get('quantity', 1)  # Default quantity is 1

                summary_lines.append(
                    f"Option Leg {index}:\n"
                    f"    Type: Call\n"
                    f"    Strike Price: ${default_strike:.2f}\n"
                    f"    Premium: ${default_premium:.2f}\n"
                    f"    Quantity: {quantity}\n"
                )
            except (IndexError, KeyError, ValueError) as e:
                summary_lines.append(f"**Option Leg {index}**: Error processing Call data: {e}")
        else:
            summary_lines.append(f"**Option Leg {index}**: Unknown option type: {data[0]}")

    # Join lines with line breaks to display each item separately
    return "\n\n".join(summary_lines)



def options_chain(symbol):
    tk = yf.Ticker(symbol)
    # Expiration dates
    exps = tk.options

    if not exps:
        st.sidebar.write("No expiration dates available for the symbol.")
        return None, pd.DataFrame()

    # Get options for each expiration
    options = pd.DataFrame()
    for e in exps:
        opt = tk.option_chain(e)
        if opt.calls.empty and opt.puts.empty:
            continue

        # Assign expirationDate to calls and puts
        calls = opt.calls.assign(expirationDate=e)
        puts = opt.puts.assign(expirationDate=e)
        options = pd.concat([options, calls, puts], ignore_index=True)


    if options.empty:
        st.write("No options data collected.")
        return None, options
        
        # Print headers
    # if not options.empty:
    #     headers = options.columns.tolist()
        # print("Options Chain Headers:", headers)
        
    # Filter out options that are in the money
    options = options[~options['inTheMoney']]
    
    # Display only headers in the terminal
    # if not options.empty:
    #     headers = options.columns.tolist()
    #     print("Filtered Options Chain Headers:", headers)
    #     print("Sample data:")
    #     print(options.head())

    # Rename and reorder columns
    options.rename(columns={
        'contractSymbol': 'Contract Name',
        'strike': 'Strike',
        'lastPrice': 'Last Price',
        'bid': 'Bid',
        'ask': 'Ask',
        'change': 'Change',
        'percentChange': '% Change',
        'volume': 'Volume',
        'openInterest': 'Open Interest',
        'impliedVolatility': 'Implied Volatility',
        'lastTradeDate': 'Last Trade Date (EDT)',
        'expirationDate': 'Expiration Date'  # Addition to align with your earlier intent
    }, inplace=True)

    columns_order = [
        'Expiration Date', 'Strike', 'Last Price', 'Contract Name', 'Bid', 'Ask', 'Change',
        '% Change', 'Volume', 'Open Interest', 'Implied Volatility',
        'Last Trade Date (EDT)'
    ]

    options = options[columns_order]
    
    return exps, options
############################################ STEAMLIT APP ####################################################

