#!/usr/bin/env python

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
from datetime import datetime
from datetime import timedelta

def main():

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
    pd.options.plotting.backend = "plotly"
    now = datetime.now()
    five_year = now - timedelta(days=1825)
    one_year = now - timedelta(days=365)
    six_month = now - timedelta(days=180)
    one_month = now - timedelta(days=30)
    two_week = now - timedelta(minutes=20160)
    one_week = now - timedelta(minutes=10080)
    one_day = now - timedelta(minutes=5760)

    sidebar = dbc.Col([
        dbc.FormGroup([
            html.Label("Enter a symbol to analyze."),
            dcc.Input(
                id='ticker-select',
                placeholder='Enter symbol',
                type='text',
                value=''
            ),
            dcc.Slider(
                id="term-slider",
                min=1,
                max=3,
                marks={1: "short-term", 2: "mid-term", 3: "long-term"},
                value=1,
            ),
            html.Label("Enter a target return amount (week)"),
            dcc.Input(
                id='target-return',
                placeholder='$',
                type='number',
                value=''
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
    ], md=3, id="sidebar", className="bg-dark text-white")

    content = dbc.Col([
        html.H3(id="time", className="text-center"),
        dcc.Interval(id="interval-component", interval=60000, n_intervals=0),
        dcc.Graph(id="time-series-chart"),
        dbc.Row([
            dbc.Col(id="term1-metrics", md=3),
            dbc.Col(id="term2-metrics", md=3),
            dbc.Col(id="term3-metrics", md=3),
            dbc.Col(id="term4-metrics", md=3),
        ], className="metrics")
    ], md=9, id="content")

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
        Output("time-series-chart", "figure"),
        Output("term1-metrics", "children"),
        Output("term2-metrics", "children"),
        Output("term3-metrics", "children"),
        Output("term4-metrics", "children"),
        Input("lookup-btn", "n_clicks"),
        State("ticker-select", "value"),
        State("term-slider", "value"))
    def update_content(n_clicks, ticker, term):
        if len(ticker) > 0:
            df = get_daily(ticker)
            if term == 1:
                terms = ["Day", "Week", "2-Week", "Month"]
            if term == 2:
                terms = ["Week", "Month", "6-Month", "Year"]
            if term == 3:
                terms = ["Month", "6-Month", "Year", "5-Year"]
            term1_vals, term2_vals, term3_vals, term4_vals = (calc(ticker, terms[i]) for i in range(4))
            #fig = px.line(df, x='date', y=['value', 'trend'])
            fig = px.line(df, x='date', y='value')
            fig.update_layout(title_text=ticker, title_x=0.5)
            #fig.update_xaxes(type='category')
            fig.update_xaxes(range=[five_year, now])
            #return fig, day_vals, week_vals, two_week_vals, month_vals, six_month_vals, year_vals
            return fig, term1_vals, term2_vals, term3_vals, term4_vals
        else:
            return px.line(data_frame=None, x=None, y =None), "", "", "", ""

    def calc(ticker, duration):
        switch = {
            "Day": one_day,
            "Week": one_week,
            "2-Week": two_week,
            "Month": one_month,
            "6-Month": six_month,
            "Year": one_year,
            "5-Year": five_year
        }
        resp, interval = ("" for i in range(2))
        vals, pos_vars, neg_vars, ret = ([] for i in range(4))
        if duration == "Day" or duration == "Week" or duration == "2-Week":
            resp = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=1min&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
            interval = "Time Series (1min)"
        else:
            resp = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
            interval = "Time Series (Daily)"
        data = json.loads(resp.content)
        for i in data[interval]:
            if datetime.fromisoformat(i.split()[0]) < switch.get(duration):
                break
            if "Daily" in interval:
                val = float(data[interval][i]["5. adjusted close"])
            else:
                o = data[interval][i]["1. open"]
                c = data[interval][i]["4. close"]
                val = (float(o) + float(c)) / 2
            vals.append(val)
        if duration == "Day":
            vals = vals[:960]
        if len(vals) > 0:
            mean = statistics.mean(vals)
            rmean = statistics.mean(vals[0:round(len(vals)*.1)])
            lmean = statistics.mean(vals[round(len(vals)*.9):])
            trend = rmean / lmean
            high = max(vals)
            low = min(vals)
            std_dev = statistics.stdev(vals, mean)
            ret.append(html.Div(duration))
            if trend > 1.01:
                ret.append(html.Div(f"Trend: {two_dec(trend)}", className="text-success"))
            elif trend < .99:
                ret.append(html.Div(f"Trend: {two_dec(trend)}", className="text-danger"))
            else:
                ret.append(html.Div(f"Trend: {two_dec(trend)}"))
            ret.append(html.Div(f"Mean: ${two_dec(mean)}"))
            ret.append(html.Div(f"High: ${two_dec(high)}"))
            ret.append(html.Div(f"Low: ${two_dec(low)}"))
            ret.append(html.Div(f"S.Dev: ${two_dec(std_dev)} ({two_dec((std_dev / mean) * 100)}%)"))
            ret.append(html.Div(f"+ Var: ${two_dec(high - mean)} ({two_dec(((high / mean) - 1) * 100)}%)"))
            ret.append(html.Div(f"- Var: ${two_dec(mean - low)} ({two_dec(((low / mean) - 1) * 100)}%)"))
        else:
            ret.append(html.Div("No Data"))
        return ret

    def get_daily(ticker):
        resp = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
        data = json.loads(resp.content)
        dates = []
        values = []
        #trends = []
        for i in data["Time Series (Daily)"]:
            close = float(data["Time Series (Daily)"][i]["5. adjusted close"])
            dates.append(i)
            values.append(close)
        '''t = (values[-1] - values[0]) / len(values)
        trends.append(values[0])
        for j in range(len(values) - 1):
            trends.append(trends[j] + t)
        #return pd.DataFrame(dict(date=dates, value=values, trend=trends))'''
        return pd.DataFrame(dict(date=dates, value=values))

    def two_dec(val):
        return "{0:.2f}".format(val)
    
    app.run_server(port='8080', debug=True)

if __name__ == "__main__":
    main()