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
#   one_day = now - timedelta(minutes=5760)

    sidebar = dbc.Col([
        dbc.FormGroup([
            html.Label("Enter symbol(s) to analyze."),
            dcc.Input(
                id='ticker-select',
                placeholder='Enter symbol',
                type='text',
                value=''
            ),
            dcc.Slider(
                id="term-slider",
                min=4,
                max=6,
                marks={4: "short-term", 6: "long-term"},
                value=4,
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
                children='Save as Default',
                color='secondary',
                block=True
            ),
        ])
    ], md=2, id="sidebar", className="bg-dark text-white")

    content = dbc.Col([
        html.Div(id="data", style={"display": "none"}),
        html.Div(id="ticker", style={"display": "none"}),
        html.H3(id="time", className="text-center"),
        dcc.Interval(
            id="interval-component",
            interval=60000,
            n_intervals=0
        ),
        dcc.Graph(id="time-series-chart"),      
        dbc.Row([
            dbc.Col(id="signal", md=3),
            dbc.Col(id="buy-price", md=3),
            dbc.Col(id="sell-price", md=3),
            dbc.Col(id="return", md=3),
        ], className="metrics")
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

    @app.callback(
        Output("alert-fade", "is_open"),
        [State("alert-fade", "is_open")],
    )
    def toggle_alert(n, is_open):
        if n:
            return not is_open
        return is_open

    # Display errors in modal
    def display_error(err):
        return dbc.Alert([
            f"Invalid input. Error was: {err}",
        ], id="alert-fade", color="danger", n_clicks=0,)


    # Get longterm time-series data from API
    @app.callback(
        Output("data", "children"),
        Output("ticker", "children"),
        Input("lookup-btn", "n_clicks"),
        State("ticker-select", "value"),
    )    
    def get_data(symbol):
        try:
            if len(symbol) < 1 or len(symbol) > 6:
                raise ValueError(f"Invalid string length for {symbol}: must be between 1 and 6 characters")
            if not symbol.isalpha():
                raise TypeError(f"Invalid input type for {symbol}: must be letters only")
            return requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol={symbol}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
        except ValueError as err:
            display_error(err)
        except TypeError as err:
            display_error(err)
        except:
            display_error("Invalid ticker symbol")

if __name__ == "__main__":
    main()