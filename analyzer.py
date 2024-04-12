#!/usr/bin/env python
#
# Description: Python Dash application to analyze time-series market data
# Version: 0.65
# Author: Brian Dunham (Netris)
#
# NOTICE: Due to AlphaVantage severly limiting their free API, this project
# will soon be converted to use the yfinance Python module. Please note that
# this module is not officially supported by Yahoo. Use at your own risk;
# abuse could result in your IP being banned

# Import modules
import re
import requests
import statistics
import json
import os
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from datetime import timedelta
from netris import fsops

def main():
    # initialize
    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
    pd.options.plotting.backend = "plotly"
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d')
    ten_year = now - timedelta(days=3650)
    five_year = now - timedelta(days=1825)
    two_year = now - timedelta(days=730)
    one_year = now - timedelta(days=365)
    six_month = now - timedelta(days=180)
    three_month = now - timedelta(days=90)
    one_month = now - timedelta(days=30)
    two_week = now - timedelta(days=14)
    one_week = now - timedelta(days=7)
    five_day = now - timedelta(days=5)
    data_dir = f"{os.getcwd()}/data"
    fsops.create_dir(data_dir)

    # Perform cleanup
    files = fsops.list_dir(data_dir)
    if files and len(files) > 1:
        for file in files:
            fn = "".join(file.split('.')[:-1]) if len(file.split('.')) > 1 else file
            if (
                len(fn.split('-')) > 1 and
                fn.split('-')[-1].isnumeric and
                now - timedelta(days=1) > datetime.strptime(fn.split('-')[-1], '%Y%m%d')
            ):
                os.remove(f"{data_dir}/{file}")

    # Dash code to build sidebar of WebUI
    sidebar = dbc.Col([
        dbc.InputGroup([
            html.Label("Enter symbol(s) to watch."),
            #dcc.Input(
            dbc.Input(
                id='watch-tickers',
                placeholder='Enter symbol(s)',
                type='text',
                pattern='[A-Za-z-=^ ,]{1,6}',
                value=''
            ),
            html.Label("Graph Scale"),
            dcc.Dropdown(
                id="term-selector",
                options=[
                    {"label": "1 Year", "value": 1},
                    {"label": "2 Year", "value": 2},
                    {"label": "5 Year", "value": 3},
                    {"label": "10 Year", "value": 4},
                ],
                value=3,
                className="text-dark",
                clearable=False
            ),
            html.Label("Graph View"),
            dcc.Dropdown(
                id="graph-selector",
                options=[
                    {"label": "Normal", "value": 1},
                    {"label": "MACD", "value": 2},
                    {"label": "Trend", "value": 3},
                    {"label": "RSI", "value": 4},
                    {"label": "OBV", "value": 5},
                    {"label": "OBV Trend", "value": 6},
                ],
                value=1,
                className="text-dark",
                clearable=False,
            ),
            html.Div([
                dbc.Button("Analyze", id="lookup-btn", n_clicks=0, color="primary"),
                dbc.Button("Save", id="save-btn", n_clicks=0, color="secondary")
            ], id="btn-div")         
        ])
    ], md=2, id="sidebar", className="bg-dark text-white")

    # Dash code to build content area of WebUI
    content = dbc.Col([
        dbc.Alert(
            "Invalid input. Error was: ",
            id="alert",
            color="danger",
            is_open=False,
            dismissable=True
        ),
        dcc.Interval(
            id="interval-component",
            interval=60000,
            n_intervals=0
        ),        
        html.H3(id="time", className="text-center"),
        dcc.Loading([
            html.Div(id="test"), # REMOVE
            html.Div(id="content"),
        ]),
    ], md=10)
    
    # Put UI Elements together
    app.layout = dbc.Container([
        dbc.Row([sidebar, content],
        className="text-dark"),
        #dcc.Store(id="data", storage_type="session")
        dcc.Loading([
            dcc.Store(id="data"),
        ]),
    ], id="container", fluid=True)

    # Update time and display at top of content area
    @app.callback(
        Output("time", "children"),
        Input("interval-component", "n_intervals")
    )
    def update_time(n):
        return datetime.now().strftime('%m/%d/%Y %H:%M')            

    # Get time-series data from API and update Dash Bootstrap components
    @app.callback(
        Output("data", "data"),
        Input("lookup-btn", "n_clicks"),
        State("watch-tickers", "value"),
        prevent_initial_call=True,
    )   
    def get_data(n_clicks, tickers):
        # Set time series data to get from API
        if len(tickers) > 1:
            data = {}
            # daily_func = "TIME_SERIES_DAILY"
            # daily_key = "Time Series (Daily)"
            weekly_func = "TIME_SERIES_WEEKLY_ADJUSTED"
            weekly_key = "Weekly Adjusted Time Series"
            file_data = fsops.read_file(f"{data_dir}/data-{timestamp}.json", type="json")
            if type(file_data) is not dict:
                file_data = {}
            changed = False
            for ticker in tickers.replace(',', ' ').split():
                ticker = ticker.upper()
                # Check if data is already present
                if file_data.get(ticker):
                    data.update({ ticker: file_data.get(ticker) })
                    continue
                # Validate ticker symbol characters and length
                elif not re.search(r'^[A-Z^]{1}[A-Z-=]{0,7}(?<=[A-Z])$', ticker):
                    return json.dumps({"error": f"Invalid characters or length in ticker: {ticker}"})
                else:
                    #dresp = requests.get(f"https://www.alphavantage.co/query?function={daily_func}&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
                    wresp = requests.get(f"https://www.alphavantage.co/query?function={weekly_func}&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
                    if (
                        #"Error Message" in json.loads(dresp.content) or
                        "Error Message" in json.loads(wresp.content)
                    ):
                        return json.dumps({"error": f"Invalid ticker in input: {ticker}"})
                    else:
                        data.update({
                            ticker: {
                                #"daily": format_data(json.loads(dresp.content).get(daily_key)),
                                "daily": {},
                                "weekly": json.loads(wresp.content).get(weekly_key),
                            }
                        })
                        changed = True
            if changed:
                file_data.update(data)
                fsops.write_file(file_data, f"{data_dir}/data-{timestamp}.json", type="json")
            return json.dumps(format_data(data))
    
    # Check for errors in data store and display bootstrap alert with error message
    @app.callback(
        Output("alert", "children"),
        Output("alert", "is_open"),
        Input("data", "data"),
        prevent_initial_call=True,
    )
    def check_data(data):
        if "error" in json.loads(data).keys():
            return json.dumps(json.loads(data).get('error')).strip('"'), True
        else:
            return dash.no_update, False
    
    # Draw graphs
    @app.callback(
        Output("content", "children"),
        Input("data", "data"),
        Input("term-selector", "value"),
        Input("graph-selector", "value"),
        prevent_initial_call=True,
    )
    def draw_graphs(data, scale, view):
        if data is not None and len(data) > 0:
            data = json.loads(data)
            graphs = []
            term_switch = {
                1: [one_year, 52],
                2: [two_year, 104],
                3: [five_year, 261],
                4: [ten_year, 521],
            }
            view_switch = {
                1: ['value buy_signal', 'rgba(0,0,0,0.5) rgba(32,208,112,0.9)'],
                2: ['macd signal', 'rgba(208,128,208,0.9) rgba(128,208,248,0.9)'],
                3: ['trend_wma trend_signal', 'rgba(0,64,224,0.9) rgba(32,208,112,0.9)'],
                4: ['rsi', 'rgba(0,0,0,0.5)'],
                5: ['obv', 'rgba(0,0,0,0.5)'],
                6: ['obv_trend obv_signal', 'rgba(0,64,224,0.9) rgba(32,208,112,0.9)'],
            } 
            for i in data:
                df = pd.read_json(data.get(i).get('weekly'), orient="split")
                params = view_switch.get(view)
                minval = min(df[params[0].split()[0]][:term_switch.get(scale)[1]]) - abs((min(df[params[0].split()[0]][:term_switch.get(scale)[1]]))*.01)
                maxval = max(df[params[0].split()[0]][:term_switch.get(scale)[1]]) + abs((max(df[params[0].split()[0]][:term_switch.get(scale)[1]]))*.01)
                fig = px.line(df, x='date', y=params[0].split()[0])
                fig.update_layout(title=i, title_x=0.5)
                fig.update_traces(line_color=params[1].split()[0])
                if len(params[0].split()) > 1:
                    for j in range(len(params[0].split())-1):
                        fig.add_scatter(x=df['date'], y=df[params[0].split()[j+1]], mode='lines', line_color=params[1].split()[j+1], line_shape='spline', name=params[0].split()[j-1])
                fig.update_xaxes(range=[term_switch.get(scale)[0], now])
                fig.update_yaxes(range=[minval, maxval])
                graphs.append(dbc.Row([
                    dcc.Graph(figure=fig, config={'displayModeBar': False}),
                    #dbc.Table.from_dataframe(df, striped=True, bordered=True, color="dark")
                ]))
            return [i for i in graphs]

    # Debugging output - REMOVE LATER!
    # @app.callback(
    #     Output("test", "children"),
    #     Input("data", "data"),
    #     prevent_initial_call=True,
    # )
    # def print_data(data):
    #     return data

    def format_data(data):
        # Calculate graphing data, format, and return as Pandas DataFram object
        h_key, l_key, close_key, adj_close_key, vol_key = "2. high", "3. low", "4. close", "5. adjusted close", "6. volume"
        for i in data.values():
            for f,j in i.items():
                dates, high, low, vol = ([] for i in range(4))
                for d,v in j.items():
                    dates.append(d)
                    adj = 1
                    if v.get(adj_close_key) and v.get(adj_close_key) != v.get(close_key):
                        adj = float(v.get(adj_close_key)) / float(v.get(close_key))
                    high.append(float(v.get(h_key)) * adj)
                    low.append(float(v.get(l_key)) * adj)
                    vol.append(int(v.get(vol_key)) / adj)
                df = pd.DataFrame({
                    "date": dates,
                    "high": high,
                    "low": low,
                    "volume": vol,
                })
                val = (df['high'] + df['low']) / 2
                df['value'] = df.index.map(val)
                lt_trend = df['value'][::-1].rolling(180).mean()
                df['lt_trend'] = df.index.map(lt_trend)
                trend_wma = df['value'][::-1].rolling(28).apply(get_wma)
                df['trend_wma'] = df.index.map(trend_wma)
                trend_signal = df['value'][::-1].ewm(span=14, min_periods=14).mean()
                df['trend_signal'] = df.index.map(trend_signal)
                get_macd(df)
                get_rsi(df)
                get_obv(df)
                obv_trend = df['obv'][::-1].rolling(28).apply(get_wma)
                df['obv_trend'] = df.index.map(obv_trend)
                obv_signal = df['obv'][::-1].ewm(span=14, min_periods=14).mean()
                df['obv_signal'] = df.index.map(obv_signal)
                get_buy_sig(df)
                i.update({f: df.to_json(date_format="iso", orient="split")})
        return data

    def get_wma(vals):
        # Calculate and return weighted moving average values for <vals>
        weights = [i+1 for i in range(len(vals))]
        return sum(weights * vals) / sum(weights)
    
    def get_rsi(df, dur=14):
        # Calculate and return RSI values from Pandas DataFrame
        delta = df['value'][::-1].diff()
        up = delta.clip(lower=0).round(2)
        down = delta.clip(upper=0).abs().round(2)
        ma_up = up.rolling(dur).mean()
        ma_down = down.rolling(dur).mean()
        rs = ma_up / ma_down
        rsi = 100 - (100 / (1 + rs ))
        df['rsi'] = df.index.map(rsi)

    def get_obv(df):
        # Calculate and return On-balance Volume from Pandas DataFrame
        delta = df['value'][::-1].diff()
        adj = delta.clip(lower=0.01, upper=-0.01).round(2) * 100
        obv = df['volume'][::-1].astype(int) * adj
        df['obv'] = df.index.map(obv.cumsum())

    def get_macd(df, fast=12, slow=26, sig=9):
        fast_ema = df['value'][::-1].ewm(span=fast, min_periods=fast).mean()
        slow_ema = df['value'][::-1].ewm(span=slow, min_periods=slow).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=sig, min_periods=sig).mean()
        df['macd'] = df.index.map(macd)
        df['signal'] = df.index.map(signal)

    def get_buy_sig(df):
        buy_sig = []
        for i, row in df.iterrows():
            if (
                row['macd'] < 1.0 and
                sum(df['macd'][i-5:i]) / 5 < 1.0 and
                round(abs(row['macd'] / row['signal']),2) in [float(x/100) for x in range(75, 125)]
                row['rsi'] < 50
            ):
                buy_sig.append(row['value'])
            else:
                buy_sig.append(-1)
        df['buy_signal'] = buy_sig  

    app.run_server(host='0.0.0.0', port='8080', debug=True)

if __name__ == "__main__":
    main()
