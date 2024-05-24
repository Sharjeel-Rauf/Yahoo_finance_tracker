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
                    f"    Average Share Cost: ${average_share_cost:.2f}\n"
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
                    f"    Default Strike Price: ${default_strike:.2f}\n"
                    f"    Default Premium: ${default_premium:.2f}\n"
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

# Display an image at the top of the sidebar
# image_path = 'images/rlt_sm.png'


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

# Clear previous inputs to avoid duplication
for key in st.session_state.keys():
    if 'shares_' in key or 'premium_' in key or 'quantity_' in key or 'share_cost_' in key or 'Strike_' in key:
        del st.session_state[key]

# Dynamically generate inputs based on strategy selection
for i, (option_type, *labels) in enumerate(option_details):
    st.sidebar.subheader(f"Option Leg {i + 1}")

    if option_type == 'Stock':
        number_of_shares = st.sidebar.number_input(labels[0], min_value=1, max_value=1000, value=100, key=f"shares_{i}")
        average_share_cost = st.sidebar.number_input(labels[1], min_value=0.01, max_value=10 * current_price, value=current_price, step=0.01, key=f"share_cost_{i}")
        options_data.append((option_type, number_of_shares, average_share_cost))
    else:
        available_strikes = selected_calls['Strike'].unique() if option_type == 'Call' else selected_puts['Strike'].unique()
        strike = st.sidebar.selectbox(labels[0], available_strikes, key=f"Strike_{i}")

        # Retrieve the last price for the selected strike price
        if strike:
            option_data = selected_calls if option_type == 'Call' else selected_puts
            last_price = option_data[option_data['Strike'] == strike]['Last Price'].iloc[0] if not option_data[option_data['Strike'] == strike].empty else 0.0

            premium = st.sidebar.number_input("Premium", min_value=0.0, max_value=1000.0, value=last_price, step=0.1, key=f"premium_{i}")
            quantity = st.sidebar.number_input("Quantity", min_value=1, max_value=100, value=1, key=f"quantity_{i}")
            options_data.append((option_type, strike, premium, quantity))



########################################
# Calculate payoff profile
def calculate_payoff(price_range, options_data):
    total_payoff = np.zeros_like(price_range)
    for data in options_data:
        if data[0] == 'Stock':
            continue  # Skip stock entries as they do not have a strike or intrinsic value calculation
        option_type, strike, premium, quantity = data
        intrinsic_values = np.maximum(price_range - strike, 0) if option_type == 'Call' else np.maximum(strike - price_range, 0)
        payoff = premium - intrinsic_values if 'Short' in option_type else intrinsic_values - premium
        total_payoff += payoff * quantity
    return total_payoff



price_range = np.linspace(0.5 * current_price, 1.5 * current_price, 400)
payoffs = calculate_payoff(price_range, options_data)

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

st.markdown("---")

# Generate the Yahoo Finance options page URL for the entered symbol
yahoo_finance_url = f"https://finance.yahoo.com/quote/{symbol}/options"
# Display the clickable link in Streamlit
# st.markdown(f"View the source data for {symbol} on [Yahoo Finance]({yahoo_finance_url})", unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader('Analysis Summary')

        # Generate and display the summary content
        summary_content = generate_summary(
            symbol, current_price, strategy, trade_duration, selected_date, options_data
        )
        st.markdown(summary_content, unsafe_allow_html=True)
    
    with col2:
        st.subheader('Trade Potentials ')
        st.write(f"Maximum potential gain: ${max_gain:.2f}")
        st.write(f"Maximum potential loss: ${max_loss:.2f}")
        st.write(f"Breakeven price: {breakeven_output}")
        
    with col3:
        st.subheader('Strategy Payoff Diagram')

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
            width=400,
            height=400
        )

        st.plotly_chart(fig, use_container_width=False)
        
st.markdown(f"View the source data for {symbol} on [Yahoo Finance]({yahoo_finance_url})",
                    unsafe_allow_html=True)