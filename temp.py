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
    two_year = now - timedelta(days=730)
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
            min=0,
            max=4,
            marks={0: "1-month", 1: "6-month", 2: "1-year", 3:"2-year", 4:"5-year"},            
            value=1,
        ),        
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
                lt_dates, lt_vals, lt_vols = ([] for i in range(3))
                for i in data_st["Time Series (1min)"]:
                    st_dates.append(i)
                    st_vals.append(data_st["Time Series (1min)"][i]["4. close"])
                    st_vols.append(data_st["Time Series (1min)"][i]["5. volume"])
                for i in data_lt["Time Series (Daily)"]:
                    lt_dates.append(i)
                    lt_vals.append(data_lt["Time Series (Daily)"][i]["5. adjusted close"])
                    lt_vols.append(data_lt["Time Series (Daily)"][i]["6. volume"])                  
                st = pd.DataFrame(dict(date=st_dates, value=st_vals, vol=st_vols))
                lt = pd.DataFrame(dict(date=lt_dates, value=lt_vals, vol=lt_vols))
                return st.to_json(date_format='iso', orient='split'), lt.to_json(date_format='iso', orient='split'), ticker.upper()
                #return json.dumps(json.loads(resp_st.content)), json.dumps(json.loads(resp_lt.content))
        else:
            return "", "", ""     

    @app.callback(
        Output("time-series-chart", "figure"),
        Input("ticker", "children"),
        Input("lt-data", "children"),
        Input("range-slider", "value"),
    )
    def update_graph(ticker, lt_data, scale):
        '''def prepare_data():
            dates, values, mas, tmas, tops, bottoms = ([] for i in range(6))
            for i in data["Time Series (Daily)"]:
                h = float(data["Time Series (Daily)"][i]["2. high"])
                l = float(data["Time Series (Daily)"][i]["3. low"])
                c = float(data["Time Series (Daily)"][i]["5. adjusted close"])
                dates.append(i)
                values.append(c)
                mas.append((h + l) / 2)
            for i in range(len(values)):
                if i == len(values) - 1:
                    tmas.append(values[i])
                    tops.append(values[i])
                    bottoms.append(values[i])
                elif i + 10 > len(values) - 1:
                    tmas.append(statistics.mean(values[i:]))
                    tops.append(statistics.mean(values[i:]) + statistics.stdev(values[i:]) * 2)
                    bottoms.append(statistics.mean(values[i:]) - statistics.stdev(values[i:]) * 2)
                else:
                    tmas.append(statistics.mean(values[i:i + 10]))              
                    tops.append(statistics.mean(values[i:i + 10]) + statistics.stdev(values[i:i + 10]) * 2)
                    bottoms.append(statistics.mean(values[i:i + 10]) - statistics.stdev(values[i:i + 10]) * 2)    
            return pd.DataFrame(dict(date=dates, value=values, ma=mas, tma=tmas, top=tops, bottom=bottoms))'''

        if len(lt_data) > 0:
            #data = json.loads(lt_data)
            df = pd.read_json(lt_data, orient='split')
            #df = prepare_data()
            switch = {
                0: [one_month, 30],
                1: [six_month, 182],
                2: [one_year, 365],
                3: [two_year, 730],
                4: [five_year, 1825],
            }
            fig = px.area(df, x='date', y='value')
            fig.update_layout(title_text=ticker, title_x=0.5)
            '''
            if statistics.mean(df['value'][0:round(switch.get(scale)[1]*.25)]) > statistics.mean(df['value'][round(switch.get(scale)[1]*.75):switch.get(scale)[1]]): 
                fig.update_traces(line_color='#40cc40')
            else:
                fig.update_traces(line_color='#cc4040')
            fig.add_scatter(x=df['date'], y=df['tma'], mode='lines', line_color='rgba(255,179,66,0.8)', line_shape='spline')
            fig.add_scatter(x=df['date'], y=df['top'], mode='lines', line_color='rgba(255,80,0,0.8)', line_shape='spline')
            fig.add_scatter(x=df['date'], y=df['bottom'], mode='lines', line_color='rgba(80,255,0,0.8)', line_shape='spline')'''
            fig.update_xaxes(range=[switch.get(scale)[0], now])
            #fig.update_yaxes(range=[min(df['value'].tolist()[:switch.get(scale)[1]]) - statistics.stdev(df['value'].tolist()[:switch.get(scale)[1]]), max(df['value'].tolist()[:switch.get(scale)[1]]) + statistics.stdev(df['value'].tolist()[:switch.get(scale)[1]])])
            fig.update_yaxes(range=[min(df['value'].tolist()[:switch.get(scale)[1]]), max(df['value'].tolist()[:switch.get(scale)[1]])])
            return fig
        else:
            return px.line(data_frame=None, x=None, y=None)
             
    @app.callback(
        #Output("time-series-chart", "figure"),
        Output("term1-metrics", "children"),
        Output("term2-metrics", "children"),
        Output("term3-metrics", "children"),
        Output("term4-metrics", "children"),
        Input("st-data", "children"),
        Input("lt-data", "children"),
        State("term-slider", "value"),
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
                6: ["5-Year", 1825]
            }
            # Generator for each term
            for t in range(term - 4, term):
                #interval = ""
                vals, highs, lows, ret = ([] for i in range(4))
                if t < 3:
                    #data = json.loads(st_data)
                    #interval = "Time Series (1min)"
                    data = pd.read_json(st_data, orient='split')
                else:
                    #data = json.loads(lt_data)
                    #interval = "Time Series (Daily)"
                    data = pd.read_json(lt_data, orient='split')
                vals = data['value'].tolist()[:switch.get(t)[1]]
                '''for i in data[interval]:
                    if datetime.fromisoformat(i.split()[0]) < switch.get(t)[1]:
                        break
                    if "Daily" in interval:
                        val = float(data[interval][i]["5. adjusted close"])
                    else:
                        #o = data[interval][i]["1. open"]
                        val = data[interval][i]["4. close"]
                        #val = (float(o) + float(c)) / 2
                    vals.append(val)
                if t == 0:
                    vals = vals[:960]'''
                if len(vals) > 0:               
                    mean = statistics.mean(vals)
                    rmean = statistics.mean(vals[0:round(len(vals)*.25)])
                    lmean = statistics.mean(vals[round(len(vals)*.75):])
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
                    skew = ((pos_var + neg_var) / mean) + 1
                    #sell = statistics.mean([(mean * skew) + std_dev, statistics.mean(highs), mean + pos_var]) * trend
                    #buy = statistics.mean([(mean * skew) - std_dev, statistics.mean(lows), mean + neg_var]) * trend
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
        
        if len(lt_data) > 0 and len(st_data) > 0:
            term1_vals, term2_vals, term3_vals, term4_vals = get_stats()
            return prep(term1_vals), prep(term2_vals), prep(term3_vals), prep(term4_vals)
        else:
            return "", "", "", ""

    def two_dec(val):
        return "{0:.2f}".format(round(val, 2))

    def four_dec(val):
        return "{0:.4f}".format(round(val, 4))
    
    app.run_server(port='8080', debug=True)

if __name__ == "__main__":
    main()