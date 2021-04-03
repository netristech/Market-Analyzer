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
                min=4,
                max=7,
                marks={4: "short-term", 7: "long-term"},
                value=4,
            ),
            html.Label("Enter a target return amount (week)"),
            dcc.Input(
                id='target-return',
                placeholder='$',
                type='number',
                value='1000'
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
        State("term-slider", "value"),
        State("target-return", "value")
    )
    def update_content(n_clicks, ticker, term, rval):

        # Function to calculate stats / metrics
        def get_stats():
            switch = {
                0: ["Day", one_day],
                1: ["Week", one_week],
                2: ["2-Week", two_week],
                3: ["Month", one_month],
                4: ["6-Month", six_month],
                5: ["Year", one_year],
                6: ["5-Year", five_year]
            }
            resp_st = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=1min&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
            resp_lt = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
            # Generator for each term
            for t in range(term - 4, term):
                interval = ""
                vals, pos_vars, neg_vars, ret = ([] for i in range(4))
                if t < 3:
                    data = json.loads(resp_st.content)
                    interval = "Time Series (1min)"
                else:
                    data = json.loads(resp_lt.content)
                    interval = "Time Series (Daily)"
                for i in data[interval]:
                    if datetime.fromisoformat(i.split()[0]) < switch.get(t)[1]:
                        break
                    if "Daily" in interval:
                        val = float(data[interval][i]["5. adjusted close"])
                    else:
                        o = data[interval][i]["1. open"]
                        c = data[interval][i]["4. close"]
                        val = (float(o) + float(c)) / 2
                    vals.append(val)
                if t == 0:
                    vals = vals[:960]
                if len(vals) > 0:               
                    mean = statistics.mean(vals)
                    rmean = statistics.mean(vals[0:round(len(vals)*.49)])
                    lmean = statistics.mean(vals[round(len(vals)*.51):])
                    trend = rmean / lmean
                    high = max(vals)
                    low = min(vals)
                    lows = [i for i in vals if i < mean]
                    highs = [i for i in vals if i > mean]
                    lows_mean = statistics.mean(lows)
                    highs_mean = statistics.mean(highs)
                    std_dev = statistics.stdev(vals, mean)
                    pos_var = highs_mean - mean
                    neg_var = lows_mean - mean
                    skew = ((pos_var + neg_var) / mean) / 2 + 1
                    sell = statistics.mean([(mean * skew) + std_dev, statistics.mean(highs), mean + (pos_var / 2)]) * trend
                    buy = statistics.mean([(mean * skew) - std_dev, statistics.mean(lows), mean + (neg_var / 2)]) * trend
                    ret = {
                        "": switch.get(t)[0],
                        "Trend": trend,
                        "Mean": mean,
                        "High": high,
                        "Low": low,
                        "S.Dev": std_dev,
                        "+ Var": pos_var,
                        "- Var": neg_var,
                        "Skew": skew
                    }
                    '''ret.append(html.Div(term))
                    if trend > 1.01:
                        ret.append(html.Div(f"Trend: {two_dec(trend)}", className="text-success"))
                    elif trend < .99:
                        ret.append(html.Div(f"Trend: {two_dec(trend)}", className="text-danger"))
                    else:
                        ret.append(html.Div(f"Trend: {two_dec(round(trend, 2))}"))
                    ret.append(html.Div(f"Mean: ${two_dec(mean)}"))
                    ret.append(html.Div(f"High: ${two_dec(high)}"))
                    ret.append(html.Div(f"Low: ${two_dec(low)}"))
                    ret.append(html.Div(f"S.Dev: ${two_dec(std_dev)} ({two_dec((std_dev / mean) * 100)}%)"))
                    ret.append(html.Div(f"+ Var: ${two_dec(pos_var)} ({two_dec(((high / mean) - 1) * 100)}%)"))
                    ret.append(html.Div(f"- Var: ${two_dec(neg_var)} ({two_dec(((low / mean) - 1) * 100)}%)"))
                    ret.append(html.Div(f"Skew: {round(skew, 4)}"))
                    ret.append(html.Div(f"Buy: ${two_dec(buy)}"))
                    ret.append(html.Div(f"Sell: ${two_dec(sell)}"))
                    ret.append(html.Div(f"Gain: ${two_dec(sell - buy)}"))
                    ret.append(html.Div(f"Shares: {two_dec(rval / (sell - buy))}"))
                    ret.append(html.Div(f"Invest: ${two_dec((rval / (sell - buy)) * buy)}"))
                else:
                    ret.append(html.Div("No Data"))
                return ret'''
                yield ret

        # Function to prepare data for display in dash
        def prep(term_vals):
            ret = []
            for i in term_vals:
                if i == "":
                    elem = html.Div(f"{term_vals.get(i)}")
                elif i == "Trend" or i == "Skew":
                    if term_vals.get(i) > 1.0:
                        elem = html.Div(f"{i}: {four_dec(term_vals.get(i))}", className="text-success")
                    elif term_vals.get(i) < 1.0:
                        elem = html.Div(f"{i}: {four_dec(term_vals.get(i))}", className="text-danger")
                    else:
                        elem = html.Div(f"{i}: {four_dec(term_vals.get(i))}")
                else:
                    elem = html.Div(f"{i}: {two_dec(term_vals.get(i))}")
                ret.append(elem)
            return ret

        # Function to produce data for Graph
        def get_graph():
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
        
        if len(ticker) > 0:
            df = get_graph()
            term1_vals, term2_vals, term3_vals, term4_vals = get_stats()
            #fig = px.line(df, x='date', y=['value', 'trend'])
            fig = px.line(df, x='date', y='value')
            fig.update_layout(title_text=ticker.upper(), title_x=0.5)
            #fig.update_xaxes(type='category')
            fig.update_xaxes(range=[five_year, now])
            return fig, prep(term1_vals), prep(term2_vals), prep(term3_vals), prep(term4_vals)
        else:
            return px.line(data_frame=None, x=None, y=None), "", "", "", ""

    def two_dec(val):
        return "{0:.2f}".format(round(val, 2))

    def four_dec(val):
        return "{0:.4f}".format(round(val, 4))
    
    app.run_server(port='8080', debug=True)

if __name__ == "__main__":
    main()