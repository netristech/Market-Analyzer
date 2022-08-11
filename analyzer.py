#!/usr/bin/env python
#
# Description: Python Dash application to analyze time-series market data
# Version: 0.65
# Author: Brian Dunham (Netris)
#

# Import modules
import re
import requests
import statistics
import simplejson as json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
#import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta

def main():
    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
    pd.options.plotting.backend = "plotly"
    key = "Weekly Adjusted Time Series"
    now = datetime.now()
    ten_year = now - timedelta(days=3650)
    five_year = now - timedelta(days=1825)
    two_year = now - timedelta(days=730)
    one_year = now - timedelta(days=365)
    six_month = now - timedelta(days=180)
    three_month = now - timedelta(days=90)
    one_month = now - timedelta(days=30)
    two_week = now - timedelta(days=14)
    one_week = now - timedelta(days=7)

    sidebar = dbc.Col([
        dbc.FormGroup([
            html.Label("Enter symbol(s) to watch."),
            dcc.Input(
                id='watch-tickers',
                placeholder='Enter symbol(s)',
                type='text',
                pattern='[A-Za-z-=^ ,]+',
                value=''
            ),           
            dcc.Slider(
                id="term-slider",
                min=1,
                max=4,
                marks={1: "1y", 2: "2y", 3: "5y", 4: "10y"},
                value=1,
            ),
            dcc.Slider(
                id="interval-slider",
                min=1,
                max=4,
                marks={1: "7/15", 2: "15/30", 3: "22/45", 4: "30/60"},
                value=1,
            ),        
            dbc.Button(
                id='lookup-btn',
                n_clicks=0,
                children='Analyze',
                color='primary',
                block=True
            ),
            dbc.Button(
                id='save-btn',
                n_clicks=0,
                children='Save',
                color='secondary',
                block=True
            ),            
        ])
    ], md=2, id="sidebar", className="bg-dark text-white")

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
            html.Div(id="test"),
            html.Div(id="content"),
        ]),
        #dcc.Graph(id="time-series-chart"),      
        #dbc.Row([
        #    dbc.Col(id="signal", md=3),
        #    dbc.Col(id="buy-price", md=3),
        #    dbc.Col(id="sell-price", md=3),
        #], className="metrics")
    ], md=10)
    
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
        if len(tickers) > 1:
            data = {}
            for ticker in tickers.replace(',', ' ').split():
                ticker = ticker.upper()
                if not re.search('^[A-Z^]{1}[A-Z-=]{0,7}(?<=[A-Z])$', ticker):
                    return json.dumps({"error": f"Invalid characters or length in ticker: {ticker}"})
                resp = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
                if "Error Message" in json.loads(resp.content):
                    return json.dumps({"error": f"Invalid ticker in input: {ticker}"})
                else:
                    data.update({ticker: format_data(json.loads(resp.content)[key])})
            return json.dumps(data)
    
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
        Input("term-slider", "value"),
        Input("interval-slider", "value"),
        prevent_initial_call=True,
    )
    def draw_graphs(data, scale, macd):
        data = json.loads(data)
        if len(data) > 0:
            graphs = []        
            term_switch = {
                1: [one_year, 52],
                2: [two_year, 104],
                3: [five_year, 261],
                4: [ten_year, 521],
            }
            int_switch = {
                1: [7, 15],
                2: [15, 30],
                3: [22, 45],
                4: [30, 60],
            }        
            for i in data:
                df = pd.read_json(data.get(i), orient="split")
                fig = px.line(df, x='date', y='value')
                fig.update_traces(line_color='rgba(0,0,0,0.5)')
                #fig.add_scatter(x=df['date'], y=get_wma(window, int_switch.get(macd)[0]), mode='lines', line_color='rgba(255,128,200,0.8)', line_shape='spline', name=f'{int_switch.get(macd)[0]} days')
                #fig.add_scatter(x=df['date'], y=get_sma(vals, int_switch.get(macd)[1]), mode='lines', line_color='rgba(128,128,255,0.8)', line_shape='spline', name=f'{int_switch.get(macd)[1]} days')
                #fig.add_scatter(x=df['date'], y=df['value'][::-1].ewm(span=int_switch.get(macd)[0], adjust=False).mean()[::-1], mode='lines', line_color='rgba(255,128,200,0.8)', line_shape='spline', name=f'{int_switch.get(macd)[0]} days')
                #fig.add_scatter(x=df['date'], y=df['value'].rolling(int_switch.get(macd)[1]).mean(), mode='lines', line_color='rgba(128,128,255,0.8)', line_shape='spline', name=f'{int_switch.get(macd)[1]} days')
                fig.update_layout(title_text=i, title_x=0.5)
                fig.update_xaxes(range=[term_switch.get(scale)[0], now])
                fig.update_yaxes(range=[min(df['value'][:term_switch.get(scale)[1]])*.99, max(df['value'][:term_switch.get(scale)[1]])*1.01])        
                graphs.append(dcc.Graph(figure=fig))
                fig = px.line(get_macd(df), x='date', y='macd')
                fig.update_traces(line_color='rgba(208,128,208,0.8)')
                fig.add_scatter(x=df['date'], y=get_macd(df)['sig'], mode='lines', line_color='rgba(128,208,248,0.8)', line_shape='spline')
                fig.update_xaxes(range=[term_switch.get(scale)[0], now])
                fig.update_yaxes(range=[min(get_macd(df)['macd'][:term_switch.get(scale)[1]])*.99, max(get_macd(df)['macd'][:term_switch.get(scale)[1]])*1.01])
                graphs.append(dcc.Graph(figure=fig))
            return html.Div([dbc.Row(i) for i in graphs])

    # Debugging output - REMOVE LATER!
    '''@app.callback(
        Output("test", "children"),
        Input("data", "data"),
        prevent_initial_call=True,
    )
    def print_data(data):
        return data'''

    # Format API data and return as Pandas DataFram object
    def format_data(data):
        dates, vals = ([] for i in range(2))
        for i in data:
            dates.append(i)
            vals.append(data[i]["5. adjusted close"])
        return pd.DataFrame(dict(date=dates, value=vals)).to_json(date_format="iso", orient="split")

    def get_wma(vals, dur):
        wvals = []
        weights = [i + 1 for i in range(dur)][::-1]
        for i in range(len(vals)):
            if i + dur >= len(vals):
                r = len(vals) - i
                w = sum([vals[-r:][x] * weights[-r:][x] for x in range(r)]) / sum(weights[-r:])
            else:
                w = sum([vals[i:i+dur][x] * weights[x] for x in range(dur)]) / sum(weights)
            wvals.append(w)
        return wvals
        
    def get_sma(vals, dur):
        svals = []
        for i in range(len(vals)):
            if i + dur >= len(vals):
                r = len(vals) - i
                s = sum(vals[-r:]) / len(vals[-r:])
            else:
                s = sum(vals[i:i+dur]) / dur
            svals.append(s)
        return svals

    def get_macd(df):
        ema12 = df['value'].ewm(span=12, adjust=False).mean()
        ema26 = df['value'].ewm(span=26, adjust=False).mean()
        df['macd'] = [round(ema12[i] - ema26[i], 2) for i in range(len(ema12))]
        df['sig'] = df['macd'].ewm(span=9, adjust=False).mean()
        return df

    app.run_server(port='8080', debug=True)

if __name__ == "__main__":
    main()