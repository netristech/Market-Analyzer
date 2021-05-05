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
#import numpy as np
from datetime import datetime
from datetime import timedelta

def main():

    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
    pd.options.plotting.backend = "plotly"
    now = datetime.now()
    five_year = now - timedelta(days=1825)
    two_year = now - timedelta(days=730)
    one_year = now - timedelta(days=365)
    six_month = now - timedelta(days=180)
    three_month = now - timedelta(days=90)
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
            #dcc.Slider(
                #id="term-slider",
                #min=4,
                #max=7,
                #marks={4: "short-term", 7: "long-term"},
                #value=4,
            #),
            html.Label("Enter a target return amount (month)"),
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
    ], md=2, id="sidebar", className="bg-dark text-white")

    content = dbc.Col([
        html.Div(id="st-data", style={"display": "none"}),
        html.Div(id="lt-data", style={"display": "none"}),
        html.Div(id="ticker", style={"display": "none"}),
        html.H3(id="time", className="text-center"),
        dcc.Interval(
            id="interval-component",
            interval=60000,
            n_intervals=0
        ),
        dcc.Graph(id="time-series-chart"),
        dcc.Slider(
            id="range-slider",
            min=4,
            max=8,
            marks={4: "1-month", 5: "6-month", 6: "1-year", 7:"2-year", 8:"5-year"},            
            value=5,
        ),        
        dbc.Row([
            dbc.Col(id="term1-metrics", md=2),
            dbc.Col(id="term2-metrics", md=2),
            dbc.Col(id="term3-metrics", md=2),
            dbc.Col(id="term4-metrics", md=2),
            dbc.Col(id="term5-metrics", md=2),
            dbc.Col(id="term6-metrics", md=2),
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
        Output("st-data", "children"),
        Output("lt-data", "children"),
        Output("ticker", "children"),
        Input("lookup-btn", "n_clicks"),
        State("ticker-select", "value"),
    )
    def store_data(n_clicks, ticker):
        if len(ticker) > 0:
            try:
                resp_st = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=1min&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
                resp_lt = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey=9LVE9OGAKH31RPWM&datatype=json")
            except:
                return "", "", ""
            else:
                data_st = json.loads(resp_st.content)
                data_lt = json.loads(resp_lt.content)
                st_dates, st_vals, st_vols = ([] for i in range(3))
                lt_dates, lt_vals, lt_vols, highs, lows = ([] for i in range(5))
                for i in data_st["Time Series (1min)"]:
                    st_dates.append(i)
                    st_vals.append(data_st["Time Series (1min)"][i]["4. close"])
                    st_vols.append(data_st["Time Series (1min)"][i]["5. volume"])
                for i in data_lt["Time Series (Daily)"]:
                    lt_dates.append(i)
                    highs.append(data_lt["Time Series (Daily)"][i]["2. high"])
                    lows.append(data_lt["Time Series (Daily)"][i]["3. low"])
                    lt_vals.append(data_lt["Time Series (Daily)"][i]["5. adjusted close"])
                    lt_vols.append(data_lt["Time Series (Daily)"][i]["6. volume"])                  
                st = pd.DataFrame(dict(date=st_dates, value=st_vals, vol=st_vols))
                lt = pd.DataFrame(dict(date=lt_dates, value=lt_vals, vol=lt_vols, high=highs, low=lows))
                return st.to_json(date_format='iso', orient='split'), lt.to_json(date_format='iso', orient='split'), ticker.upper()
        else:
            return "", "", ""     

    @app.callback(
        Output("time-series-chart", "figure"),
        Input("ticker", "children"),
        Input("lt-data", "children"),
        Input("range-slider", "value"),
    )
    def update_graph(ticker, lt_data, scale):
        if len(lt_data) > 0:
            df = pd.read_json(lt_data, orient='split')
            switch = {
                4: [one_month, 30],
                5: [six_month, 182],
                6: [one_year, 365],
                7: [two_year, 730],
                8: [five_year, 1825],
            }
            fig = px.line(df, x='date', y='value')
            fig.update_traces(line_color='rgba(0,0,0,0.5)')
            fig.update_layout(title_text=ticker, title_x=0.5)
            '''
            if statistics.mean(df['value'][0:round(switch.get(scale)[1]*.25)]) > statistics.mean(df['value'][round(switch.get(scale)[1]*.75):switch.get(scale)[1]]): 
                fig.update_traces(line_color='#40cc40')
            else:
                fig.update_traces(line_color='#cc4040')
            fig.add_scatter(x=df['date'], y=df['tma'], mode='lines', line_color='rgba(255,179,66,0.8)', line_shape='spline')
            fig.add_scatter(x=df['date'], y=df['top'], mode='lines', line_color='rgba(255,80,0,0.8)', line_shape='spline')
            fig.add_scatter(x=df['date'], y=df['bottom'], mode='lines', line_color='rgba(80,255,0,0.8)', line_shape='spline')'''
            fig.add_scatter(x=pd.concat([df['date'], df['date'][::-1]]), y=pd.concat([df['high'], df['low'][::-1]]), mode='lines', line_color='rgba(80,120,255,1)', line_shape='spline', fill='toself', fillcolor='rgba(80,120,255,0.5)', hoveron='points', name='Range')
            fig.update_xaxes(range=[switch.get(scale)[0], now])
            fig.update_yaxes(range=[min(df['low'].tolist()[:switch.get(scale)[1]]), max(df['high'].tolist()[:switch.get(scale)[1]])])
            return fig
        else:
            return px.line(data_frame=None, x=None, y=None)
             
    @app.callback(
        #Output("time-series-chart", "figure"),
        Output("term1-metrics", "children"),
        Output("term2-metrics", "children"),
        Output("term3-metrics", "children"),
        Output("term4-metrics", "children"),
        Output("term5-metrics", "children"),
        Output("term6-metrics", "children"),
        Input("st-data", "children"),
        Input("lt-data", "children"),
        Input("range-slider", "value"),
        #State("term-slider", "value"),
        State("target-return", "value")
    )
    def update_content(st_data, lt_data, term, rval):
        # Function to calculate stats / metrics
        def get_stats():
            switch = {
                0: ["Day", 960],
                1: ["Week", 4800],
                2: ["2-Week", 9600],
                3: ["Month", 30],
                4: ["6-Month", 180],
                5: ["Year", 365],
                6: ["2-Year", 720],
                7: ["5-Year", 1825]
            }
            # Generator for each term
            if term < 6:
                r = 6
            else:
                r = term
            for t in range(r - 6, r):
                vals, highs, lows, ret = ([] for i in range(4))
                if t < 3:
                    data = pd.read_json(st_data, orient='split')
                else:
                    data = pd.read_json(lt_data, orient='split')
                vals = data['value'].tolist()[:switch.get(t)[1]]
                if len(vals) > 0:              
                    mean = statistics.fmean(vals)
                    rval = statistics.fmean(vals[0:round(len(vals)*.25)])
                    lval = statistics.fmean(vals[round(len(vals)*.75):])
                    trend = rval / lval
                    high = max(vals)
                    low = min(vals)
                    lows = [i for i in vals if i < mean]
                    highs = [i for i in vals if i > mean]
                    lows_mean = statistics.fmean(lows)
                    highs_mean = statistics.fmean(highs)
                    std_dev = statistics.stdev(vals, mean)
                    pos_var = highs_mean - mean
                    neg_var = lows_mean - mean
                    skew = ((pos_var + neg_var) / mean) + 1
                    #sell = statistics.mean([(mean * skew) + std_dev, statistics.mean(highs), mean + pos_var]) * trend
                    #buy = statistics.mean([(mean * skew) - std_dev, statistics.mean(lows), mean + neg_var]) * trend
                    wvals = []
                    d = 0
                    for i in range(len(vals)):
                        wvals.append(vals[i] * (len(vals) - i))
                        d += len(vals) - i
                    wma = sum(wvals) / d
                    '''q1 = statistics.fmean(vals[:round(len(vals)*.25)])
                    q2 = statistics.fmean(vals[round(len(vals)*.25):round(len(vals)*.5)])
                    q3 = statistics.fmean(vals[round(len(vals)*.5):round(len(vals)*.75)])
                    q4 = statistics.fmean(vals[round(len(vals)*.75):])
                    wma1 = sum([q1*4,q2*3,q3*2,q4]) / 10
                    wma2 = sum([q1*3,q2*2,q3]) / 6
                    wma3 = sum([q1*2,q2]) / 3
                    if wma3 > wma1:
                        if wma3 / wma2 > wma2 / wma1:
                            sig = 'hold'
                        else:
                            sig = 'sell'
                    else:
                        if wma3 / wma2 < wma2 / wma1:
                            sig = 'wait'
                        else:
                            sig = 'buy'''
                    ret = {
                        "Title": switch.get(t)[0],
                        "Trend": trend,
                        "Mean": mean,
                        "High": high,
                        "Low": low,
                        "S.Dev": std_dev,
                        "+ Var": pos_var,
                        "- Var": neg_var,
                        "Skew": skew,
                        "WMA": wma,
                        #"Signal": sig,
                    }
                yield ret

        # Function to prepare data for display in dash
        def prep(term_vals):
            ret = []
            for i in term_vals:
                if i == "Title":
                    elem = html.Div(f"{term_vals.get(i)}", style={"font-weight": "bold"})
                elif i == "Trend" or i == "Skew":
                    if term_vals.get(i) > 1.0:
                        elem = html.Div(f"{i}: {four_dec(term_vals.get(i))}", className="text-success")
                    elif term_vals.get(i) < 1.0:
                        elem = html.Div(f"{i}: {four_dec(term_vals.get(i))}", className="text-danger")
                    else:
                        elem = html.Div(f"{i}: {four_dec(term_vals.get(i))}")
                elif i == "Signal":
                    elem = html.Div(f"{i}: {term_vals.get(i)}")
                else:
                    elem = html.Div(f"{i}: {two_dec(term_vals.get(i))}")
                ret.append(elem)
            return ret        
        
        if len(lt_data) > 0 and len(st_data) > 0:
            term1_vals, term2_vals, term3_vals, term4_vals, term5_vals, term6_vals = get_stats()

            return prep(term1_vals), prep(term2_vals), prep(term3_vals), prep(term4_vals), prep(term5_vals), prep(term6_vals)
        else:
            return "", "", "", "", "", ""

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

    def get_obv(vals, vols):
        ovals = vals[::-1]
        ovols = vols[::-1]
        obvals = [ovols[0]]
        for i in range(len(ovals)-1):
            if ovals[i+1] > ovals[i]:
                obvals.append(obvals[i] + ovols[i+1])
            else:
                obvals.append(obvals[i] - ovols[i+1])
        return obvals[::-1]

    def two_dec(val):
        return "{0:.2f}".format(round(val, 2))

    def four_dec(val):
        return "{0:.4f}".format(round(val, 4))
    
    app.run_server(port='8080', debug=True)

if __name__ == "__main__":
    main()