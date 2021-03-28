#!/usr/bin/env python

import requests
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px

def main():
    response = requests.get("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=GME&interval=5min&apikey=9LVE9OGAKH31RPWM")
    app = dash.Dash()
    colors = {
        'background': '#f2f2f2',
        'text': '#484848'
    }   
    app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
        html.H1(
            children='Hello Dash',
            style={
                'textAlign': 'center',
                'color': colors['text']
            }
        ),
        html.Div(children=str(response.json()), style={
            'textAlign': 'center',
            'color': colors['text']
        }),
        dcc.Graph(
            id='Graph1',
            figure={
                'data': [
                    {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                    {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
                ],
                'layout': {
                    'plot_bgcolor': colors['background'],
                    'paper_bgcolor': colors['background'],
                    'font': {
                        'color': colors['text']
                    }
                }
            }
        )
    ])
    app.run_server(debug=True)
    df = px.data.stocks()
    fig = px.line(df, x='date', y="GOOG")
    fig.show()

if __name__ == "__main__":
    main()
