#!/usr/bin/env python
#
# Description: Python Dash application to analyze time-series market data
# Version: 0.5
# Author: Brian Dunham (Netris)
#

# Import modules
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
    now = datetime.now()
    ten_year = now - timedelta(days=3650)
    five_year = now - timedelta(days=1825)
    two_year = now - timedelta(days=730)
    one_year = now - timedelta(days=365)
    six_month = now - timedelta(days=180)
    three_month = now - timedelta(days=90)
    one_month = now - timedelta(days=30)
    two_week = now - timedelta(minutes=20160)
    one_week = now - timedelta(minutes=10080)

    sidebar = dbc.Col([
        dbc.FormGroup([
            html.Label("Enter symbol(s) to analyze."),
            dcc.Input(
                id='ticker-select',
                placeholder='Enter symbol',
                type='text',
                value=''
            ),
            dbc.Button(
                id='lookup-btn',
                n_clicks=0,
                children='Analyze',
                color='primary',
                block=True
            ),
        ])
    ], md=2, id="sidebar", className="bg-dark text-white")

    content = dbc.Col([
        #html.Div(id="data", style={"display": "none"}),
        #html.Div(id="ticker", style={"display": "none"}),
        dbc.Alert(
            "Invalid input. Error was: ",
            id="alert",
            color="danger",
            is_open=False,
            dismissable=True
        ),
        html.Div(id="data"),
        dcc.Interval(
            id="interval-component",
            interval=60000,
            n_intervals=0
        ),        
        html.Div(id="ticker"),
        html.H3(id="time", className="text-center"),
        #dcc.Graph(id="time-series-chart"),      
        #dbc.Row([
        #    dbc.Col(id="signal", md=3),
        #    dbc.Col(id="buy-price", md=3),
        #    dbc.Col(id="sell-price", md=3),
        #], className="metrics")
    ], md=10, id="content")
    
    app.layout = dbc.Container([
        dbc.Row([sidebar, content],
        className="text-dark")
    ], id="container", fluid=True)

    @app.callback(
        Output("time", "children"),
        Input("interval-component", "n_intervals")
    )
    def update_time(n):
        return datetime.now().strftime('%m/%d/%Y %H:%M')       

    # Get time-series data from API and update Dash Bootstrap components
    @app.callback(
        Output("data", "children"),
        Output("alert", "children"),
        Output("alert", "is_open"),
        Input("lookup-btn", "n_clicks"),
        State("ticker-select", "value"),
    )    
    def get_data(n_clicks, ticker):
        if len(ticker) < 1 or len(ticker) > 6:
            return dash.no_update, f"Invalid string length ({ticker}): must be between 1 and 6 characters", True
        if not ticker.isalpha():
            return dash.no_update, f"Invalid input type ({ticker}): must be letters only", True
        try:
            return format_data(requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")), dash.no_update, False
        except:
            return dash.no_update, f"Invalid symbol: {ticker}", True

    # Format data and return as Pandas DataFram object             
    def format_data(resp):
        data = json.loads(resp.content)
        dates, vals = ([] for i in range(2))
        for i in data["Weekly Adjusted Time Series"]:
            dates.append(i)
            vals.append(data["Weekly Adjusted Time Series"][i]["5. adjusted close"])
        return pd.DataFrame(dict(date=dates, value=vals)).to_json(date_format='iso', orient='split')

    app.run_server(port='8080', debug=True)

if __name__ == "__main__":
    main()