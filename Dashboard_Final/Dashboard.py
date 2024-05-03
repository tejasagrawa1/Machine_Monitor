# File to create the dashboard and reltated functions

# Import necessary libraries
import dash
from dash import dcc
from dash import html
from dash import no_update
import plotly.graph_objs as go
import csv
import json
import os
import numpy as np
import tensorflow as tf
import shutil
from datetime import datetime, timedelta, date
from dash.dependencies import Input, Output, State
from threading import Timer, Thread
from Treon_to_model_Mac import split_function, Main, cancel_data

# Create Dashboard Class
class Dashboard:
    # Initialise the class
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=['style.css'])  # Initialize the Dash application with the current module name and an external stylesheet for CSS customisation
        self.last_update_time_global = datetime.now()   # Get the date-time at the initialisation
        self.value = 0  # Set current fault status. 0 for no faults detected
        self.archive_value = 0  # set the archive fault status. Will be changed when a dataset is archived for the history tab
        self.set_number # Set the value of the first set number. Takes form SET{set_number}_BC{base_condition}
        self.base_condition = 0 # Set the value of the first set base condition. Takes form SET{set_number}_BC{base_condition}
        self.fft_data = None    # initialise path to fft.csv file to retrive fft data to None 
        self.sensor_data = None # initialise path to test.csv file to retrive sensor data to None 
        self.model_data = None  # initialise path to fft.csv file to retrive fft data to None to use in ML model
        self.date_time = None   # Initialise date_time to None to be used when renaming data set file by date-time when archiving to history
        self.chosen_date = None # Initialse output of chosen date using Dash's DatePickerSingle component in the history tab to None
        self.dropdown_path = None   # Intitialise the path of the chosen data from dropdown menu in the in the history tab to None
        self.status_file_path = None # Intitialise the file path for the archived status value to None
        self.base_directory = os.path.join(os.getcwd(), 'Collected_Data') # Initialise the Base Directory
        self.setup_layout() # Initialise setup_layout function to setup the dashboard
        self.register_callbacks()   # Initialise the register_callbacks function to update components in the dashboard

        # Set the HTML template for the entire Dash app. This template defines the overall HTML structure
        # that will be rendered in the browser. 
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
            <style>
                html, body {
                    margin: 0;
                    padding: 0;
                    background-color: #111525;
                    height: 100%;
                    width: 100%;
                }
            </style>
        </html>
        '''

    # Function to setup the layout and html of the dashboard 
    def setup_layout(self):
        self.app.layout = html.Div(className='bg-colour', children=[
            # Creating tabs diffault being the home dashboard
            dcc.Tabs(id='tabs',  value='dashboard', children=[
                # Creating home tab 
                dcc.Tab(label='DASHBOARD', id='tab-1', children=[
                    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-around', 'alignItems': 'flex-start'}, children=[
                        # creating left row division. Displaying Sensor 1 data and fft plots in x,y,z axis
                        html.Div([
                            html.H2('SENSOR 1', className='header-font text-colour', style={'textAlign': 'center', 'font-size': '2em', 'margin-top': '0px'}),
                            dcc.Graph(id='fft-plot-x1', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0'}),
                            dcc.Graph(id='fft-plot-y1', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            dcc.Graph(id='fft-plot-z1', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.Div(id='hidden-div', style={'display': 'none'}),
                                        html.P('ROOT MEAN SQUARE (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='rms-1', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-x1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-y1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-z1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('KURTOSIS', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='kurtosis-1', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-x1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-y1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-z1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                                ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),

                                html.Div([
                                    html.Div([
                                        html.P('PEAK-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='p2p-1', children=[
                                            html.Div([
                                              html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                              html.Span('0.00', id='p2p-value-x1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                              html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                              html.Span('0.00', id='p2p-value-y1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                              html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                              html.Span('0.00', id='p2p-value-z1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('ZERO-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='z2p-1', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-x1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-y1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-z1', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                               ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),
                            ], style={'width': '100%'}),
                        ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '30px',
                                  'margin': '25px 0', 'width': '30%', 'minWidth': '300px', 'margin-top': '20px',
                                  'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),

                        # creating middle row division. Displaying start, stop buttons, time information, fault status & sensor details
                        html.Div([
                            html.Div([
                                html.Button("Start", id="play-button", n_clicks=0, className='header-font button-normal-play'),
                                dcc.Store(id='button-state', data={'play': False, 'terminate': False})
                            ], style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '10px'}),
                            html.Div([
                                html.Button("Stop", id="stop-button", n_clicks=0, className='header-font button-normal-stop'),
                                dcc.Store(id='button-state-stop', data={'stop': False, 'terminate': False})
                            ], style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '20px'}),
                            html.Div([
                                dcc.Store(id='timestamp-store', storage_type='local'),  # Use local storage to persist across refreshes
                                dcc.Interval(
                                    id='interval-component',
                                    interval=1000,  # in milliseconds
                                    n_intervals=0
                                ),
                                html.H3(id='time', className='header-font text-colour', style={'textAlign': 'center'}),
                                html.H3(id='next-update', className='header-font text-colour', style={'textAlign': 'center'}),
                                html.H3(id='last-updated', className='header-font text-colour', style={'textAlign': 'center'}),
                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '5px',
                                  'margin': '10px 0', 'width': '100%', 'minWidth': '300px', 'margin-top': '20px',
                                    'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),

                            html.Div([
                                # Green circle indicator
                                html.Div('NO FAULTS DETECTED', id='faults-status', className='header-font', style={
                                    'border': '12px solid #28A745',  # Ring color and thickness
                                    'border-radius': '50%',  # Round the corners to make it a circle
                                    'color': '#28A745',  # Text color
                                    'font-size': '24px',  # Adjust font size
                                    'height': '275px',  # Circle size, including border
                                    'width': '275px',
                                    'display': 'flex',
                                    'align-items': 'center',  # Center the text vertically
                                    'justify-content': 'center',  # Center the text horizontally
                                    'margin': '0 auto',  # Center the circle horizontally in the div
                                    'background-color': 'transparent',  # Make the inside of the circle transparent
                                }),
                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '30px',
                                      'margin': '10px 0', 'width': '85%', 'minWidth': '300px', 'margin-top': '20px',
                                        'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),
                            html.Div([
                                html.Div([
                                    html.Img(src='/assets/Sensor1_Image.png', style={'width': '40%', 'height': 'auto',
                                                               'margin-left': '-10px', 'margin-top': '-5px'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '300px'}),
                                html.Div([
                                    html.H3('SENSOR 1', className='header-font text-colour', style={'display': 'inline-block'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '300px', 'marginTop': '10px'}),
                                html.Div([
                                    html.P('NODE ID:', className='header-font text-colour', style={'margin-left': '5px', 'margin-top': '-10px'}),
                                    html.P(id='node-id-1', className='header-font text-colour', style={'margin-left': '100px', 'margin-top': '-35px'}),
                                ], style={'max-width': '185px', 'margin-left': '140px', 'margin-top': '-150px',
                                          'border': '2px solid #2391C0', 'padding': '10px', 'borderRadius': '5px',
                                          'marginBottom': '5px', 'backgroundColor': '#111525'}),
                                html.Div([
                                    html.Div(style={'display': 'flex', 'alignItems': 'center', 'border': '2px solid #2391C0',
                                                    'padding': '10px', 'borderRadius': '5px', 'marginBottom': '10px', 'backgroundColor': '#111525'}, children=[
                                        html.P('BATTERY LEVEL', className='header-font text-colour', style={'marginRight': '10px'}),
                                        html.Div(className='battery-container', style={'display': 'flex', 'alignItems': 'center'}, children=[
                                            html.Div(id='battery-symbol-1', className='battery-symbol', style={'display': 'inline-block'}, children=[
                                                html.Div(id='battery-filling-1', className='battery-filling')
                                            ]),
                                            html.Div('100%', id='battery-percentage-1', className='battery-percentage header-font', style={'display': 'inline-block', 'marginLeft': '8px'})
                                        ])
                                    ])
                                ], style={'maxWidth': '200px', 'marginLeft': '140px', 'marginTop': '20px'}),

                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '20px',
                                      'margin': '10px 0', 'width': '90%', 'minWidth': '300px', 'min-height': '150px',
                                      'marginTop': '20px', 'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),
                            html.Div([
                                html.Div([
                                    html.Img(src='/assets/Sensor2_Image.png', style={'width': '65%', 'height': 'auto',
                                            'margin-left': '-5px', 'margin-top': '-5px'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '175px'}),
                                html.Div([
                                    html.H3('SENSOR 2', className='header-font text-colour', style={'display': 'inline-block'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '300px', 'marginTop': '10px'}),
                                html.Div([
                                    html.P('NODE ID:', className='header-font text-colour', style={'margin-left': '5px', 'margin-top': '-10px'}),
                                    html.P(id='node-id-2', className='header-font text-colour', style={'margin-left': '100px', 'margin-top': '-35px'}),
                                ], style={'max-width': '185px', 'margin-left': '140px', 'margin-top': '-155px',
                                          'border': '2px solid #2391C0', 'padding': '10px', 'borderRadius': '5px',
                                          'backgroundColor': '#111525'}),
                                html.Div([
                                    html.Div(style={'display': 'flex', 'alignItems': 'center', 'border': '2px solid #2391C0',
                                                    'padding': '10px', 'borderRadius': '5px', 'marginBottom': '10px',
                                                    'backgroundColor': '#111525'}, children=[
                                        html.P('BATTERY LEVEL:', className='header-font text-colour', style={'marginRight': '10px'}),
                                        html.Div(className='battery-container', style={'display': 'flex', 'alignItems': 'center'}, children=[
                                            html.Div(id='battery-symbol-2', className='battery-symbol', style={'display': 'inline-block'}, children=[
                                                html.Div(id='battery-filling-2', className='battery-filling')
                                            ]),
                                            html.Div('100%', id='battery-percentage-2', className='battery-percentage header-font', style={'display': 'inline-block', 'marginLeft': '8px'})
                                        ])
                                    ])
                                ], style={'maxWidth': '200px', 'marginLeft': '140px', 'marginTop': '20px'}),

                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '20px',
                                      'margin': '10px 0', 'width': '90%', 'minWidth': '300px', 'min-height': '150px',
                                      'marginTop': '20px', 'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),
                        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),

                        # creating right row division. Displaying Sensor 2 data and fft plots in x,y,z axis
                        html.Div([
                            html.H2('SENSOR 2', className='header-font text-colour', style={'textAlign': 'center', 'font-size': '2em', 'margin-top': '0px'}),
                            dcc.Graph(id='fft-plot-x2', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0'}),
                            dcc.Graph(id='fft-plot-y2', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            dcc.Graph(id='fft-plot-z2', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.P('ROOT MEAN SQUARE (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='rms-2', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-x2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-y2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-z2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('KURTOSIS', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='kurtosis-2', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-x2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-y2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-z2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                                ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),
                                html.Div([
                                    html.Div([
                                        html.P('PEAK-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='p2p-2', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='p2p-value-x2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='p2p-value-y2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='p2p-value-z2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('ZERO-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='z2p-2', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-x2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-y2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-z2', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                                ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),
                            ], style={'width': '100%'}),
                        ], className='card-bg-colour' , style={'border-radius': '5px', 'padding': '30px',
                                'margin': '25px 0', 'width': '30%', 'minWidth': '300px', 'margin-top': '20px',
                                'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'})
                    ])
                ], className='tab-default tab-selected header-font ', value='dashboard'),

                # Creating the history tab
                dcc.Tab(label='HISTORY', id='tab-2', children=[
                    html.Div(className='bg-colour', children=[
                        # Creating Date Picker
                        dcc.DatePickerSingle(
                            id='my-date-picker-single',
                            date=date.today(),
                            display_format='YYYY-MM-DD',
                            className='header-font',
                            style={'marginRight': '10px', 'padding': '10px'}
                        ),

                        html.Div(id='output-date', style={'display': 'none'}),

                        #html.Div(id='dropdown-container'),
                        html.Div(id='dummy-dropdown', style={'display': 'none'}),

                        # Creating Dropdown Menu to choose available data on a particular date based on time
                        dcc.Dropdown(
                            id='my-dropdown',
                            options=[],
                            placeholder="Select",
                            className='header-font',
                            style={'width': '300px', 'verticalAlign': 'middle'}
                        )
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),

                    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-around', 'alignItems': 'flex-start'}, children=[
                        # creating left row division. Displaying Sensor 1 data and fft plots in x,y,z axis
                        html.Div([
                            html.H2('SENSOR 1', className='header-font text-colour', style={'textAlign': 'center', 'font-size': '2em', 'margin-top': '0px'}),
                            dcc.Graph(id='fft-plot-x1h', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0'}),
                            dcc.Graph(id='fft-plot-y1h', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            dcc.Graph(id='fft-plot-z1h', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.P('ROOT MEAN SQUARE (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='rms-1h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-x1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-y1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-z1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('KURTOSIS', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='kurtosis-1h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-x1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-y1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-z1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                                ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),

                                html.Div([
                                    html.Div([
                                        html.P('PEAK-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='p2p-1h', children=[
                                            html.Div([
                                              html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                              html.Span('0.00', id='p2p-value-x1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                              html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                              html.Span('0.00', id='p2p-value-y1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                              html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                              html.Span('0.00', id='p2p-value-z1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('ZERO-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='z2p-1h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-x1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-y1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-z1h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                               ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),
                            ], style={'width': '100%'}),
                        ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '30px',
                                  'margin': '25px 0', 'width': '30%', 'minWidth': '300px', 'margin-top': '20px',
                                  'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),

                        # creating middle row division. Displaying start, stop buttons, time information, fault status & sensor details
                        html.Div([
                            html.Div([
                                # Green circle indicator
                                html.Div('NO FAULTS DETECTED', id='faults-status-h', className='header-font', style={
                                    'border': '12px solid #28A745',  # Ring color and thickness
                                    'border-radius': '50%',  # Round the corners to make it a circle
                                    'color': '#28A745',  # Text color
                                    'font-size': '24px',  # Adjust font size
                                    'height': '275px',  # Circle size, including border
                                    'width': '275px',
                                    'display': 'flex',
                                    'align-items': 'center',  # Center the text vertically
                                    'justify-content': 'center',  # Center the text horizontally
                                    'margin': '0 auto',  # Center the circle horizontally in the div
                                    'background-color': 'transparent',  # Make the inside of the circle transparent
                                }),
                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '30px',
                                      'margin': '10px 0', 'width': '85%', 'minWidth': '300px', 'margin-top': '20px',
                                        'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),
                            html.Div([
                                html.Div([
                                    html.Img(src='/assets/Sensor1_Image.png', style={'width': '40%', 'height': 'auto',
                                                               'margin-left': '-10px', 'margin-top': '-5px'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '300px'}),
                                html.Div([
                                    html.H3('SENSOR 1', className='header-font text-colour', style={'display': 'inline-block'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '300px', 'marginTop': '10px'}),
                                html.Div([
                                    html.P('NODE ID:', className='header-font text-colour', style={'margin-left': '5px', 'margin-top': '-10px'}),
                                    html.P(id='node-id-1h', className='header-font text-colour', style={'margin-left': '100px', 'margin-top': '-35px'}),
                                ], style={'max-width': '185px', 'margin-left': '140px', 'margin-top': '-150px',
                                          'border': '2px solid #2391C0', 'padding': '10px', 'borderRadius': '5px',
                                          'marginBottom': '5px', 'backgroundColor': '#111525'}),
                                html.Div([
                                    html.Div(style={'display': 'flex', 'alignItems': 'center', 'border': '2px solid #2391C0',
                                                    'padding': '10px', 'borderRadius': '5px', 'marginBottom': '10px', 'backgroundColor': '#111525'}, children=[
                                        html.P('BATTERY LEVEL', className='header-font text-colour', style={'marginRight': '10px'}),
                                        html.Div(className='battery-container', style={'display': 'flex', 'alignItems': 'center'}, children=[
                                            html.Div(id='battery-symbol-1h', className='battery-symbol', style={'display': 'inline-block'}, children=[
                                                html.Div(id='battery-filling-1h', className='battery-filling')
                                            ]),
                                            html.Div('100%', id='battery-percentage-1h', className='battery-percentage header-font', style={'display': 'inline-block', 'marginLeft': '8px'})
                                        ])
                                    ])
                                ], style={'maxWidth': '200px', 'marginLeft': '140px', 'marginTop': '20px'}),
                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '20px',
                                      'margin': '10px 0', 'width': '90%', 'minWidth': '300px', 'min-height': '150px',
                                      'marginTop': '20px', 'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),
                            html.Div([
                                html.Div([
                                    html.Img(src='/assets/Sensor2_Image.png', style={'width': '65%', 'height': 'auto',
                                            'margin-left': '-5px', 'margin-top': '-5px'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '175px'}),
                                html.Div([
                                    html.H3('SENSOR 2', className='header-font text-colour', style={'display': 'inline-block'}),
                                ], style={'display': 'flex','justify-content': 'flex-start', 'align-items': 'flex-start',
                                          'maxWidth': '300px', 'marginTop': '10px'}),
                                html.Div([
                                    html.P('NODE ID:', className='header-font text-colour', style={'margin-left': '5px', 'margin-top': '-10px'}),
                                    html.P(id='node-id-2h', className='header-font text-colour', style={'margin-left': '100px', 'margin-top': '-35px'}),
                                ], style={'max-width': '185px', 'margin-left': '140px', 'margin-top': '-155px',
                                          'border': '2px solid #2391C0', 'padding': '10px', 'borderRadius': '5px',
                                          'backgroundColor': '#111525'}),
                                html.Div([
                                    html.Div(style={'display': 'flex', 'alignItems': 'center', 'border': '2px solid #2391C0',
                                                    'padding': '10px', 'borderRadius': '5px', 'marginBottom': '10px',
                                                    'backgroundColor': '#111525'}, children=[
                                        html.P('BATTERY LEVEL:', className='header-font text-colour', style={'marginRight': '10px'}),
                                        html.Div(className='battery-container', style={'display': 'flex', 'alignItems': 'center'}, children=[
                                            html.Div(id='battery-symbol-2h', className='battery-symbol', style={'display': 'inline-block'}, children=[
                                                html.Div(id='battery-filling-2h', className='battery-filling')
                                            ]),
                                            html.Div('100%', id='battery-percentage-2h', className='battery-percentage header-font', style={'display': 'inline-block', 'marginLeft': '8px'})
                                        ])
                                    ])
                                ], style={'maxWidth': '200px', 'marginLeft': '140px', 'marginTop': '20px'}),
                            ], className='card-bg-colour', style={'border-radius': '5px', 'padding': '20px',
                                      'margin': '10px 0', 'width': '90%', 'minWidth': '300px', 'min-height': '150px',
                                      'marginTop': '20px', 'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'}),
                        ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),

                        # creating right row division. Displaying Sensor 2 data and fft plots in x,y,z axis
                        html.Div([
                            html.H2('SENSOR 2', className='header-font text-colour', style={'textAlign': 'center', 'font-size': '2em', 'margin-top': '0px'}),
                            dcc.Graph(id='fft-plot-x2h', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0'}),
                            dcc.Graph(id='fft-plot-y2h', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            dcc.Graph(id='fft-plot-z2h', style={'height': '300px', 'width': '100%', 'border-radius': '5px', 'border': '3px solid #2391C0', 'margin-top': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.P('ROOT MEAN SQUARE (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='rms-2h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-x2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-y2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='rms-value-z2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('KURTOSIS', className='header-font text-colour', style={'textAlign': 'center', 'margin-top': '10px', 'fontSize':'18px'}),
                                        html.Div(id='kurtosis-2h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-x2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-y2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='kurtosis-value-z2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                                ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),
                                html.Div([
                                    html.Div([
                                        html.P('PEAK-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='p2p-2h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='p2p-value-x2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='p2p-value-y2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'fontSize':'20px'}),
                                                html.Span('0.00', id='p2p-value-z2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),

                                    html.Div([
                                        html.P('ZERO-TO-PEAK (mm/s)', className='header-font text-colour', style={'textAlign': 'center', 'fontSize':'18px'}),
                                        html.Div(id='z2p-2h', children=[
                                            html.Div([
                                                html.P('X', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-x2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center'}),
                                            html.Div([
                                                html.P('Y', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-y2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'}),
                                            html.Div([
                                                html.P('Z', className='header-font text-colour', style={'margin-left': '16px', 'fontSize':'20px'}),
                                                html.Span('0.00', id='z2p-value-z2h', className='digital-font', style={'display': 'inline-block'}),
                                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '20px'})
                                        ]),
                                    ], style={'width': '50%', 'display': 'inline-block'}),
                                ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin-top': '20px'}),
                            ], style={'width': '100%'}),
                        ], className='card-bg-colour' , style={'border-radius': '5px', 'padding': '30px',
                                'margin': '25px 0', 'width': '30%', 'minWidth': '300px', 'margin-top': '20px',
                                'box-shadow': '0 10px 8px rgba(0, 0, 0, 0.7)'})
                    ])
                ], className='tab-default header-font', value='history')
            ]),
        ])

    def register_callbacks(self):

        """
        Registers callback functions for the Dash application. Callbacks in Dash are used to update
        UI components based on user interactions or other events. This method sets up all the logic
        for interaction within the application, such as button clicks, tab changes, or data updates
        based on timers. Callbacks are defined using the app.callback decorator, where inputs and
        outputs are specified. Inputs trigger the callback, and outputs are the components that
        get updated by the callback function.
        """

        # Callback for updating the time display and triggering events at set intervals
        @self.app.callback(
            [Output('time', 'children'),
             Output('next-update', 'children'),
             Output('last-updated', 'children'),
             Output('timestamp-store', 'data')],
            [Input('interval-component', 'n_intervals')],
            [State('timestamp-store', 'data'), State('button-state', 'data')]
        )

        def update_time_and_countdown(n, stored_data, button_state):
            """
            Updates the current time display, manages countdown to the next data update, and
            maintains last updated time. The callback is triggered by an interval component,
            making it execute periodically.
            """

            now = datetime.now()
            current_time_str = 'CURRENT TIME: ' + now.strftime('%H:%M:%S')

            play_active = button_state.get('play', False) if button_state else False

            if not play_active:
                # Before the play button is pressed, reset the last update time to ensure it starts fresh
                last_update_time = now
                store_data = {
                    'last_update': last_update_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'first_update_done': False  # Track if the first update after play has been done
                }
                return current_time_str, "NEXT UPDATE: 05:00:00", "LAST UPDATED: --:--:--", store_data

            last_update_str = stored_data.get('last_update', now.strftime('%Y-%m-%d %H:%M:%S.%f'))
            last_update_time = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S.%f')
            first_update_done = stored_data.get('first_update_done', False)

            time_elapsed = now - last_update_time
            countdown = timedelta(minutes=5) - time_elapsed

            if countdown.total_seconds() <= 0:
                countdown = timedelta(minutes=5)
                last_update_time = now
                first_update_done = True  # Mark that the first update has been completed
                store_data = {
                    'last_update': last_update_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'first_update_done': first_update_done
                }
            else:
                store_data = {
                    'last_update': last_update_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'first_update_done': first_update_done
                }

            countdown_str = 'NEXT UPDATE: {:02d}:{:02d}:{:02d}'.format(
                int(countdown.total_seconds() // 3600),
                int((countdown.total_seconds() % 3600) // 60),
                int(countdown.total_seconds() % 60)
            )

            # Only display the last updated time if the first update has been done
            last_updated_str = 'LAST UPDATED: ' + last_update_time.strftime('%H:%M:%S') if first_update_done else "LAST UPDATED: --:--:--"

            return current_time_str, countdown_str, last_updated_str, store_data

        # Callback for switching tab styles based on the selected tab    
        @self.app.callback(
            [Output('tab-1', 'className'),
             Output('tab-2', 'className')],
            [Input('tabs', 'value')]
        )
        def update_tab_styles(selected_tab_value):
            """
            Dynamically updates CSS classes of tabs to reflect which tab is currently selected.
            This helps in enhancing the UI to show active/inactive tabs.
            """

            if selected_tab_value == 'dashboard':
                # Dashboard is selected, History is not
                return 'tab-default tab-selected header-font', 'tab-default header-font'
            else:
                # History is selected, Dashboard is not
                return 'tab-default header-font', 'tab-default tab-selected header-font'

        # Callback for updating all sensor & fft values & fault status in the dashboard
        @self.app.callback(
            [Output('rms-value-x1', 'children'),
             Output('rms-value-y1', 'children'),
             Output('rms-value-z1', 'children'),
             Output('kurtosis-value-x1', 'children'),
             Output('kurtosis-value-y1', 'children'),
             Output('kurtosis-value-z1', 'children'),
             Output('p2p-value-x1', 'children'),
             Output('p2p-value-y1', 'children'),
             Output('p2p-value-z1', 'children'),
             Output('z2p-value-x1', 'children'),
             Output('z2p-value-y1', 'children'),
             Output('z2p-value-z1', 'children'),
             Output('node-id-1', 'children'),

             Output('rms-value-x2', 'children'),
             Output('rms-value-y2', 'children'),
             Output('rms-value-z2', 'children'),
             Output('kurtosis-value-x2', 'children'),
             Output('kurtosis-value-y2', 'children'),
             Output('kurtosis-value-z2', 'children'),
             Output('p2p-value-x2', 'children'),
             Output('p2p-value-y2', 'children'),
             Output('p2p-value-z2', 'children'),
             Output('z2p-value-x2', 'children'),
             Output('z2p-value-y2', 'children'),
             Output('z2p-value-z2', 'children'),
             Output('node-id-2', 'children'),

             Output('fft-plot-x1', 'figure'),
             Output('fft-plot-y1', 'figure'),
             Output('fft-plot-z1', 'figure'),
             Output('fft-plot-x2', 'figure'),
             Output('fft-plot-y2', 'figure'),
             Output('fft-plot-z2', 'figure'),

             Output('faults-status', 'children'),
             Output('faults-status', 'style')
             ],
            [Input('interval-component', 'n_intervals')],
            [State('button-state', 'data')]
        )
        def update_sensor_values(n_intervals, button_state):
            if not button_state.get('play', False):
                raise dash.exceptions.PreventUpdate
            else:
                if os.listdir(self.base_directory):
                    self.update_data_paths_sensor()
                    sensor_data = self.load_sensor_data_from_csv()
                    if sensor_data:  # Check if there's any data
                        first_sensor_data = sensor_data[0]
                        second_sensor_data = sensor_data[1]
                        self.date_time = first_sensor_data['date_time']
                        self.archive_dataset()
                    
                    self.update_data_paths_fft()
                    # Load the FFT data from CSV
                    fft_data = self.load_fft_data_from_csv()

                    # Initialize empty figures
                    fig1 = go.Figure()
                    fig2 = go.Figure()
                    fig3 = go.Figure()
                    fig4 = go.Figure()
                    fig5 = go.Figure()
                    fig6 = go.Figure()

                    if fft_data:
                        sensor_1_data_x = [x if x >= 0 else None for x in fft_data[0]['FFT_X']]
                        sensor_1_data_y = [y if y >= 0 else None for y in fft_data[0]['FFT_Y']]
                        sensor_1_data_z = [z if z >= 0 else None for z in fft_data[0]['FFT_Z']]
                        sensor_2_data_x = [x if x >= 0 else None for x in fft_data[1]['FFT_X']]
                        sensor_2_data_y = [y if y >= 0 else None for y in fft_data[1]['FFT_Y']]
                        sensor_2_data_z = [z if z >= 0 else None for z in fft_data[1]['FFT_Z']]

                        # Create the plots
                        fig1.add_trace(go.Scatter(y=sensor_1_data_x, mode='lines', name='Sensor 1 FFT', line=dict(color='#ff00eb')))
                        fig2.add_trace(go.Scatter(y=sensor_1_data_y, mode='lines', name='Sensor 1 FFT', line=dict(color='#f39c12')))
                        fig3.add_trace(go.Scatter(y=sensor_1_data_z, mode='lines', name='Sensor 1 FFT', line=dict(color='#28d746')))

                        fig4.add_trace(go.Scatter(y=sensor_2_data_x, mode='lines', name='Sensor 1 FFT', line=dict(color='#ff00eb')))
                        fig5.add_trace(go.Scatter(y=sensor_2_data_y, mode='lines', name='Sensor 1 FFT', line=dict(color='#f39c12')))
                        fig6.add_trace(go.Scatter(y=sensor_2_data_z, mode='lines', name='Sensor 1 FFT', line=dict(color='#28d746')))

                        background_color = 'rgba(0,0,0,0)'

                        fig1.update_layout(
                            title='Sensor 1 FFT Plot X',
                            xaxis_title='Frequency (Hz)',
                            yaxis_title='Amplitude',
                            plot_bgcolor= background_color,  # Set the plot background color
                            paper_bgcolor='#111525',  # Set the paper background color
                            font=dict(color="white")  # Set the font color if you have a dark background
                        )

                        fig2.update_layout(
                            title='Sensor 1 FFT Plot Y',
                            xaxis_title='Frequency (Hz)',
                            yaxis_title='Amplitude',
                            plot_bgcolor=background_color,
                            paper_bgcolor='#111525',
                            font=dict(color="white")
                        )

                        fig3.update_layout(
                            title='Sensor 1 FFT Plot Z',
                            xaxis_title='Frequency (Hz)',
                            yaxis_title='Amplitude',
                            plot_bgcolor=background_color,
                            paper_bgcolor='#111525',
                            font=dict(color="white")
                        )

                        fig4.update_layout(
                            title='Sensor 2 FFT Plot X',
                            xaxis_title='Frequency (Hz)',
                            yaxis_title='Amplitude',
                            plot_bgcolor=background_color,
                            paper_bgcolor='#111525',
                            font=dict(color="white")
                        )

                        fig5.update_layout(
                            title='Sensor 2 FFT Plot Y',
                            xaxis_title='Frequency (Hz)',
                            yaxis_title='Amplitude',
                            plot_bgcolor=background_color,
                            paper_bgcolor='#111525',
                            font=dict(color="white")
                        )

                        fig6.update_layout(
                            title='Sensor 2 FFT Plot Z',
                            xaxis_title='Frequency (Hz)',
                            yaxis_title='Amplitude',
                            plot_bgcolor=background_color,
                            paper_bgcolor='#111525',
                            font=dict(color="white")
                        )
                
                    self.update_data_paths_model()
                    self.load_data_to_model()
                    self.save_fault_status(self.status_file_path, self.value)
                    if self.value is None:
                        # The predicted category hasn't been set yet
                        raise dash.exceptions.PreventUpdate
                    else:
                        value = str(self.value)
                        if os.path.isdir("Collected_Data/SET0_BC0"): shutil.rmtree("Collected_Data/SET0_BC0")
                        if value == '0':  # No fault
                                return (
                                    first_sensor_data['RMS_x'],
                                    first_sensor_data['RMS_y'],
                                    first_sensor_data['RMS_z'],
                                    first_sensor_data['Kurtosis_x'],
                                    first_sensor_data['Kurtosis_y'],
                                    first_sensor_data['Kurtosis_z'],
                                    first_sensor_data['P2P_x'],
                                    first_sensor_data['P2P_y'],
                                    first_sensor_data['P2P_z'],
                                    first_sensor_data['Z2P_x'],
                                    first_sensor_data['Z2P_y'],
                                    first_sensor_data['Z2P_z'],
                                    first_sensor_data['sensor_id'],

                                    second_sensor_data['RMS_x'],
                                    second_sensor_data['RMS_y'],
                                    second_sensor_data['RMS_z'],
                                    second_sensor_data['Kurtosis_x'],
                                    second_sensor_data['Kurtosis_y'],
                                    second_sensor_data['Kurtosis_z'],
                                    second_sensor_data['P2P_x'],
                                    second_sensor_data['P2P_y'],
                                    second_sensor_data['P2P_z'],
                                    second_sensor_data['Z2P_x'],
                                    second_sensor_data['Z2P_y'],
                                    second_sensor_data['Z2P_z'],
                                    second_sensor_data['sensor_id'],

                                    # Return the figures to the graphs
                                    fig1, fig2, fig3, fig4, fig5, fig6, 

                                    'NO FAULTS DETECTED', {
                                        'border': '12px solid #28A745',  # Ring color and thickness
                                        'border-radius': '50%',  # Round the corners to make it a circle
                                        'color': '#28A745',  # Text color
                                        'font-size': '24px',  # Adjust font size
                                        'height': '275px',  # Circle size, including border
                                        'width': '275px',
                                        'display': 'flex',
                                        'align-items': 'center',  # Center the text vertically
                                        'justify-content': 'center',  # Center the text horizontally
                                        'margin': '0 auto',  # Center the circle horizontally in the div
                                        'background-color': 'transparent',  # Make the inside of the circle transparent
                                    }
                                )  
                        else:
                            fault_dict = {
                                '1': 'No Run',
                                '2': 'Loose Foundation',
                                '3': 'Uneven Base',
                                '4': 'Overload'
                            }
                            
                            return (
                                    first_sensor_data['RMS_x'],
                                    first_sensor_data['RMS_y'],
                                    first_sensor_data['RMS_z'],
                                    first_sensor_data['Kurtosis_x'],
                                    first_sensor_data['Kurtosis_y'],
                                    first_sensor_data['Kurtosis_z'],
                                    first_sensor_data['P2P_x'],
                                    first_sensor_data['P2P_y'],
                                    first_sensor_data['P2P_z'],
                                    first_sensor_data['Z2P_x'],
                                    first_sensor_data['Z2P_y'],
                                    first_sensor_data['Z2P_z'],
                                    first_sensor_data['sensor_id'],

                                    second_sensor_data['RMS_x'],
                                    second_sensor_data['RMS_y'],
                                    second_sensor_data['RMS_z'],
                                    second_sensor_data['Kurtosis_x'],
                                    second_sensor_data['Kurtosis_y'],
                                    second_sensor_data['Kurtosis_z'],
                                    second_sensor_data['P2P_x'],
                                    second_sensor_data['P2P_y'],
                                    second_sensor_data['P2P_z'],
                                    second_sensor_data['Z2P_x'],
                                    second_sensor_data['Z2P_y'],
                                    second_sensor_data['Z2P_z'],
                                    second_sensor_data['sensor_id'],

                                    # Return the figures to the graphs
                                    fig1, fig2, fig3, fig4, fig5, fig6, 

                                    fault_dict.get(value, 'Unknown Fault'), {
                                        'border': '12px solid #FF0000',  # Red border
                                        'color': '#FF0000',  # Red text
                                        'animation': 'blinker 1s linear infinite',  # Blinking effect
                                        'border-radius': '50%',  # Round the corners to make it a circle
                                        'font-size': '30px',  # Adjust font size
                                        'height': '275px',  # Circle size, including border
                                        'width': '275px',
                                        'display': 'flex',
                                        'align-items': 'center',  # Center the text vertically
                                        'justify-content': 'center',  # Center the text horizontally
                                        'margin': '0 auto',  # Center the circle horizontally in the div
                                        'background-color': 'transparent',  # Make the inside of the circle transparent
                                    }
                                )                   
                else:
                    # Not time to update, so do not change the values.
                    raise dash.exceptions.PreventUpdate
        
        # Callback for updating the states of the Play Button
        @self.app.callback(
            [Output('play-button', 'className'),
             Output('button-state', 'data')],
            [Input('play-button', 'n_clicks')],
            [State('button-state', 'data')]
        )

        def update_button_styles(play_clicks, button_state):
            """
            This callback function toggles the state of the play button between 'play' and 'stop'.
            It adjusts the visual style of the button based on its state and manages a thread that
            clears local SQL database & connects to the MQTT Server and retrive the data sets when the play button is active.
            """
            ctx = dash.callback_context

            if not ctx.triggered:
                # This is the initial load
                button_state = button_state or {'play': False, 'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'first_run': True}
                play_style = 'button-clicked-play' if button_state['play'] else 'button-normal-play'
                return play_style, button_state

            # Toggle the state based on the previous state
            button_state['play'] = not button_state['play']
            button_state['first_run'] = True  # Reset first run on state toggle

            # Decide the class based on the current state
            play_style = 'button-clicked-play' if button_state['play'] else 'button-normal-play'
           
            if button_state['play']:
                # Start Main in a thread
                thread = Thread(target=self.threaded_main)
                thread.daemon = True  # Optional: Makes the thread exit when the main program does
                thread.start()
            
            return play_style, button_state
        
        # Callback to update the output Div
        @self.app.callback(
            Output('output-date', 'children'),
            Input('my-date-picker-single', 'date')
        )
        def update_output(selected_date):
            if selected_date is not None:
                self.chosen_date = selected_date
                return f"Selected Date: {selected_date}"
            else:
                return "No date selected"
            
        @self.app.callback(
            Output('my-dropdown', 'options'),  # Update the options
            [Input('my-date-picker-single', 'date'),
             Input('interval-component', 'n_intervals')],
            [State('button-state', 'data')]
        )
        def update_dropdown_options(selected_date, n_intervals, button_state):
            if selected_date is None:
                return no_update  # Keep the existing options if no date is selected

            # Path to the "History_Data" folder
            folder_path = 'History_Data'
            
            # Initialize empty list for dropdown options
            time_options = []
            
            try:
                # List all folders in the directory
                for folder_name in os.listdir(folder_path):
                    date_part, time_part = folder_name.split('_')
                    
                    # Check if the folder's date matches the selected date
                    if date_part == selected_date:
                        display_time = time_part.replace('-', ':')
                        time_options.append({'label': display_time, 'value': time_part})
                        
                # Handle the case when no folders match the selected date
                if not time_options:
                    time_options.append({'label': 'No data available', 'value': 'None'})

            except Exception as e:
                print(f"Error reading directory: {str(e)}")
                return no_update  # Return existing options if there's an error

            return time_options
        
        @self.app.callback(
            Output('dummy-dropdown', 'children'),  # You might not need to update anything on the page
            Input('my-dropdown', 'value')
        )
        def update_folder_path(selected_value):
            if selected_value:
                # Assume `selected_value` corresponds directly to a folder name or path segment
                base_path = 'History_Data'  # Define the base path where folders are stored
                folder_path = self.chosen_date + '_' + selected_value
                self.dropdown_path = os.path.join(base_path, folder_path)
            return no_update  # Or you can update some hidden Div if needed to trigger further callbacks
        
        @self.app.callback(
            [Output('rms-value-x1h', 'children'),
             Output('rms-value-y1h', 'children'),
             Output('rms-value-z1h', 'children'),
             Output('kurtosis-value-x1h', 'children'),
             Output('kurtosis-value-y1h', 'children'),
             Output('kurtosis-value-z1h', 'children'),
             Output('p2p-value-x1h', 'children'),
             Output('p2p-value-y1h', 'children'),
             Output('p2p-value-z1h', 'children'),
             Output('z2p-value-x1h', 'children'),
             Output('z2p-value-y1h', 'children'),
             Output('z2p-value-z1h', 'children'),
             Output('node-id-1h', 'children'),

             Output('rms-value-x2h', 'children'),
             Output('rms-value-y2h', 'children'),
             Output('rms-value-z2h', 'children'),
             Output('kurtosis-value-x2h', 'children'),
             Output('kurtosis-value-y2h', 'children'),
             Output('kurtosis-value-z2h', 'children'),
             Output('p2p-value-x2h', 'children'),
             Output('p2p-value-y2h', 'children'),
             Output('p2p-value-z2h', 'children'),
             Output('z2p-value-x2h', 'children'),
             Output('z2p-value-y2h', 'children'),
             Output('z2p-value-z2h', 'children'),
             Output('node-id-2h', 'children')
             ],
            [Input('my-dropdown', 'value')]
        )
        def update_sensor_values_history(selected_folder):
            if selected_folder:
                sensor_data = self.load_sensor_data_from_csv_history()
                if sensor_data:  # Check if there's any data
                    first_sensor_data = sensor_data[0]
                    second_sensor_data = sensor_data[1]
                    return (first_sensor_data['RMS_x'],
                            first_sensor_data['RMS_y'],
                            first_sensor_data['RMS_z'],
                            first_sensor_data['Kurtosis_x'],
                            first_sensor_data['Kurtosis_y'],
                            first_sensor_data['Kurtosis_z'],
                            first_sensor_data['P2P_x'],
                            first_sensor_data['P2P_y'],
                            first_sensor_data['P2P_z'],
                            first_sensor_data['Z2P_x'],
                            first_sensor_data['Z2P_y'],
                            first_sensor_data['Z2P_z'],
                            first_sensor_data['sensor_id'],

                            second_sensor_data['RMS_x'],
                            second_sensor_data['RMS_y'],
                            second_sensor_data['RMS_z'],
                            second_sensor_data['Kurtosis_x'],
                            second_sensor_data['Kurtosis_y'],
                            second_sensor_data['Kurtosis_z'],
                            second_sensor_data['P2P_x'],
                            second_sensor_data['P2P_y'],
                            second_sensor_data['P2P_z'],
                            second_sensor_data['Z2P_x'],
                            second_sensor_data['Z2P_y'],
                            second_sensor_data['Z2P_z'],
                            second_sensor_data['sensor_id'],
                            )
                else:
                    # No data found, do not update the component values.
                    return no_update
            else:
                    # No data found, do not update the component values.
                    return no_update    
            
        @self.app.callback(
            [Output('fft-plot-x1h', 'figure'),
             Output('fft-plot-y1h', 'figure'),
             Output('fft-plot-z1h', 'figure'),
             Output('fft-plot-x2h', 'figure'),
             Output('fft-plot-y2h', 'figure'),
             Output('fft-plot-z2h', 'figure')],
            [Input('my-dropdown', 'value')]
        )
        def update_fft_plots_history(selected_folder):
            if selected_folder:
                # Load the FFT data from CSV
                fft_data = self.load_fft_data_from_csv_history()

                # Initialize empty figures
                fig1 = go.Figure()
                fig2 = go.Figure()
                fig3 = go.Figure()
                fig4 = go.Figure()
                fig5 = go.Figure()
                fig6 = go.Figure()

                if fft_data:
                    sensor_1_data_x = [x if x >= 0 else None for x in fft_data[0]['FFT_X']]
                    sensor_1_data_y = [y if y >= 0 else None for y in fft_data[0]['FFT_Y']]
                    sensor_1_data_z = [z if z >= 0 else None for z in fft_data[0]['FFT_Z']]
                    sensor_2_data_x = [x if x >= 0 else None for x in fft_data[1]['FFT_X']]
                    sensor_2_data_y = [y if y >= 0 else None for y in fft_data[1]['FFT_Y']]
                    sensor_2_data_z = [z if z >= 0 else None for z in fft_data[1]['FFT_Z']]

                    # Create the plots
                    fig1.add_trace(go.Scatter(y=sensor_1_data_x, mode='lines', name='Sensor 1 FFT', line=dict(color='#ff00eb')))
                    fig2.add_trace(go.Scatter(y=sensor_1_data_y, mode='lines', name='Sensor 1 FFT', line=dict(color='#f39c12')))
                    fig3.add_trace(go.Scatter(y=sensor_1_data_z, mode='lines', name='Sensor 1 FFT', line=dict(color='#28d746')))

                    fig4.add_trace(go.Scatter(y=sensor_2_data_x, mode='lines', name='Sensor 1 FFT', line=dict(color='#ff00eb')))
                    fig5.add_trace(go.Scatter(y=sensor_2_data_y, mode='lines', name='Sensor 1 FFT', line=dict(color='#f39c12')))
                    fig6.add_trace(go.Scatter(y=sensor_2_data_z, mode='lines', name='Sensor 1 FFT', line=dict(color='#28d746')))

                    background_color = 'rgba(0,0,0,0)'

                    fig1.update_layout(
                        title='Sensor 1 FFT Plot X',
                        xaxis_title='Frequency (Hz)',
                        yaxis_title='Amplitude',
                        plot_bgcolor= background_color,  # Set the plot background color
                        paper_bgcolor='#111525',  # Set the paper background color
                        font=dict(color="white")  # Set the font color if you have a dark background
                    )

                    fig2.update_layout(
                        title='Sensor 1 FFT Plot Y',
                        xaxis_title='Frequency (Hz)',
                        yaxis_title='Amplitude',
                        plot_bgcolor=background_color,
                        paper_bgcolor='#111525',
                        font=dict(color="white")
                    )

                    fig3.update_layout(
                        title='Sensor 1 FFT Plot Z',
                        xaxis_title='Frequency (Hz)',
                        yaxis_title='Amplitude',
                        plot_bgcolor=background_color,
                        paper_bgcolor='#111525',
                        font=dict(color="white")
                    )

                    fig4.update_layout(
                        title='Sensor 2 FFT Plot X',
                        xaxis_title='Frequency (Hz)',
                        yaxis_title='Amplitude',
                        plot_bgcolor=background_color,
                        paper_bgcolor='#111525',
                        font=dict(color="white")
                    )

                    fig5.update_layout(
                        title='Sensor 2 FFT Plot Y',
                        xaxis_title='Frequency (Hz)',
                        yaxis_title='Amplitude',
                        plot_bgcolor=background_color,
                        paper_bgcolor='#111525',
                        font=dict(color="white")
                    )

                    fig6.update_layout(
                        title='Sensor 2 FFT Plot Z',
                        xaxis_title='Frequency (Hz)',
                        yaxis_title='Amplitude',
                        plot_bgcolor=background_color,
                        paper_bgcolor='#111525',
                        font=dict(color="white")
                    )
                # Return the figures to the graphs
                return fig1, fig2, fig3, fig4, fig5, fig6
            else:
                return no_update
            
        # Callback to update faul status section in the history tab    
        @self.app.callback(
                [Output('faults-status-h', 'children'),
                Output('faults-status-h', 'style')],
                [Input('my-dropdown', 'value')]
        )
        def update_fault_status_history(selected_folder):
            if selected_folder:    
                # Construct the path to the fault status JSON file
                path = os.path.join(self.dropdown_path, 'fault_status.json')

                # Check if the file exists
                if not os.path.exists(path):
                    print("Fault status file not found.")
                    raise dash.exceptions.PreventUpdate

                # Read the fault status from the JSON file
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        self.archive_value = data['fault_status']
                except Exception as e:
                    print(f"Error reading fault status: {e}")
                    raise dash.exceptions.PreventUpdate

                # Use the loaded value to update the display
                value = str(self.archive_value)
                if value == '0':  # No fault
                    return 'NO FAULTS DETECTED', {
                        'border': '12px solid #28A745',  # Ring color and thickness
                        'border-radius': '50%',  # Round the corners to make it a circle
                        'color': '#28A745',  # Text color
                        'font-size': '24px',  # Adjust font size
                        'height': '275px',  # Circle size, including border
                        'width': '275px',
                        'display': 'flex',
                        'align-items': 'center',  # Center the text vertically
                        'justify-content': 'center',  # Center the text horizontally
                        'margin': '0 auto',  # Center the circle horizontally in the div
                        'background-color': 'transparent',  # Make the inside of the circle transparent
                    }
                else:
                    fault_dict = {
                        '1': 'No Run',
                        '2': 'Loose Foundations',
                        '3': 'Uneven Base',
                        '4': 'Overload'
                    }
                    return fault_dict.get(value, 'Unknown Fault'), {
                        'border': '12px solid #FF0000',  # Red border
                        'color': '#FF0000',  # Red text
                        'animation': 'blinker 1s linear infinite',  # Blinking effect
                        'border-radius': '50%',  # Round the corners to make it a circle
                        'font-size': '30px',  # Adjust font size
                        'height': '275px',  # Circle size, including border
                        'width': '275px',
                        'display': 'flex',
                        'align-items': 'center',  # Center the text vertically
                        'justify-content': 'center',  # Center the text horizontally
                        'margin': '0 auto',  # Center the circle horizontally in the div
                        'background-color': 'transparent',  # Make the inside of the circle transparent
                    }
            else:
                # If no folder is selected, do not update anything
                raise dash.exceptions.PreventUpdate

    # Function to get sensor data from csv file
    def load_sensor_data_from_csv(self):
        results = []
        with open(self.sensor_data, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                sensor_data = {
                    'sensor_id': row['Sensor_id'],
                    'P2P_x': row['X_P2P'],
                    'P2P_y': row['Y_P2P'],
                    'P2P_z': row['Z_P2P'],
                    'RMS_x': row['X_RMS'],
                    'RMS_y': row['Y_RMS'],
                    'RMS_z': row['Z_RMS'],
                    'Z2P_x': row['X_Z2P'],
                    'Z2P_y': row['Y_Z2P'],
                    'Z2P_z': row['Z_Z2P'],
                    'Kurtosis_x': row['X_Kurtosis'],
                    'Kurtosis_y': row['Y_Kurtosis'],
                    'Kurtosis_z': row['Z_Kurtosis'],
                    'date_time': row['Date_time']
                }
                results.append(sensor_data)
        return results

    # Function to get fft data from csv file
    def load_fft_data_from_csv(self):
        results = []
        with open(self.fft_data, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Assuming the FFT_dictionary column contains a string that can be converted to a dictionary
                fft_dict_str = row['FFT_dictionary']
                # Convert the string representation of a dictionary to an actual dictionary
                fft_dict = json.loads(fft_dict_str.replace("'", "\""))  # Making sure single quotes are replaced with double quotes for valid JSON
                fft_data = {
                    'sensor_id': row['Sensor_id'],
                    'FFT_X': fft_dict['FFT_X'],  # Extract the FFT_X values
                    'FFT_Y': fft_dict['FFT_Y'],  # Extract the FFT_Y values
                    'FFT_Z': fft_dict['FFT_Z']  # Extract the FFT_Y values
                }
                results.append(fft_data)
        return results

    # Function to update the path for the test.csv to obtain sensor data
    def update_data_paths_sensor(self):
        base_path = os.path.join('Collected_Data', f'SET{self.set_number}_BC{self.base_condition}')
        self.sensor_data = os.path.join(base_path, 'test.csv')

    # Function to update the path for the fft.csv to obtain fft data
    def update_data_paths_fft(self):
        base_path = os.path.join('Collected_Data', f'SET{self.set_number}_BC{self.base_condition}')
        self.fft_data = os.path.join(base_path, 'fft.csv')

    # Function to uodate path to for the fft data for the model's use
    def update_data_paths_model(self):
        base_path = os.path.join('Collected_Data', f'SET{self.set_number}_BC{self.base_condition}')
        self.model_data = base_path

    # Function to load fft data into ML Model and do a prediction
    def load_data_to_model(self):
        model = tf.keras.models.load_model("ModelCNN_2D_Final.h5")

        X_predict=[] 
        data_file = os.path.join(self.model_data, 'fft.csv')
        with open(data_file, newline='') as f:
                        reader = csv.reader(f)
                        data = list(reader)[1:]  # Remove header
                        data_sensor1 = json.loads(data[0][2])
                        data_sensor2 = json.loads(data[1][2])
                        Input_set = [data_sensor1['FFT_X'], data_sensor1['FFT_Y'], data_sensor1['FFT_Z'],
                                        data_sensor2['FFT_X'], data_sensor2['FFT_Y'], data_sensor2['FFT_Z']]
                        X_predict=Input_set
        X_predict = np.array(X_predict)      
        X_predict = X_predict.reshape(-1, 6, 980, 1)
        predictions = model.predict(X_predict)
        predicted_categories = np.argmax(predictions, axis=1)
        self.value = int(predicted_categories)          

    # Function to archive dataset to use in the history tab
    def archive_dataset(self):
        base_path = os.path.join('Collected_Data', f'SET{self.set_number}_BC{self.base_condition}')

        history_folder = os.path.join(os.getcwd(), 'History_Data')
        if not os.path.exists(history_folder):
            os.makedirs(history_folder)

        # Set the destination file path
        if self.date_time:
            # Format or clean the date_time_str to be a valid filename if necessary
            safe_date_time_str = self.date_time.replace(':', '-').replace(' ', '_')
            destination_dir_path = os.path.join(history_folder, safe_date_time_str)

        # Check if the file exists and then copy it
        if os.path.exists(base_path):
            try:
                # Copy the file to the new location with the new name
                shutil.copytree(base_path, destination_dir_path)
                print(f'Directory copied to {destination_dir_path}')
                self.create_fault_status_json(destination_dir_path)
                return no_update
            except Exception as e:
                print(f'Failed to copy directory: {e}')
                return no_update
        else:
            print('No Directory found to copy')
            return no_update
        
    # Function to retrieve sensor data from csv file    
    def load_sensor_data_from_csv_history(self):
        results = []
        path = os.path.join(self.dropdown_path, 'test.csv')
        with open(path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                sensor_data = {
                    'sensor_id': row['Sensor_id'],
                    'P2P_x': row['X_P2P'],
                    'P2P_y': row['Y_P2P'],
                    'P2P_z': row['Z_P2P'],
                    'RMS_x': row['X_RMS'],
                    'RMS_y': row['Y_RMS'],
                    'RMS_z': row['Z_RMS'],
                    'Z2P_x': row['X_Z2P'],
                    'Z2P_y': row['Y_Z2P'],
                    'Z2P_z': row['Z_Z2P'],
                    'Kurtosis_x': row['X_Kurtosis'],
                    'Kurtosis_y': row['Y_Kurtosis'],
                    'Kurtosis_z': row['Z_Kurtosis'],
                    'date_time': row['Date_time']
                }
                results.append(sensor_data)
        return results

    # Function to retrieve fft data from csv file    
    def load_fft_data_from_csv_history(self):
        results = []
        path = os.path.join(self.dropdown_path, 'fft.csv')
        with open(path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Assuming the FFT_dictionary column contains a string that can be converted to a dictionary
                fft_dict_str = row['FFT_dictionary']
                # Convert the string representation of a dictionary to an actual dictionary
                fft_dict = json.loads(fft_dict_str.replace("'", "\""))  # Making sure single quotes are replaced with double quotes for valid JSON
                fft_data = {
                    'sensor_id': row['Sensor_id'],
                    'FFT_X': fft_dict['FFT_X'],  # Extract the FFT_X values
                    'FFT_Y': fft_dict['FFT_Y'],  # Extract the FFT_Y values
                    'FFT_Z': fft_dict['FFT_Z']  # Extract the FFT_Y values
                }
                results.append(fft_data)
        return results
    
    # Function to save fault value in fault_status.json in archived data set for the history tab
    def save_fault_status(self, directory, status):
        with open(directory, 'w') as f:
            json.dump({'fault_status': status}, f)

    # Function to create fault_status.json inside archived dataset
    def create_fault_status_json(self, directory):
        self.status_file_path = os.path.join(directory, 'fault_status.json')
        with open(self.status_file_path, 'w') as file:
            pass    

    # Function to define the thread to run when play button is pressed to run the Main() function
    def threaded_main(self):
        while True:
            # Start the timer and Main function when the play button is pressed
            t1 = Timer(interval=300, function=split_function)
            t1.start()
            Main()       

    # Function to run the dashboard
    def run(self, debug=True):
        # First empty local sql database 
        cancel_data()
        # Path to the "Collected_Data" folder
        folder_path = os.path.join(os.getcwd(), 'Collected_Data')

        # Check if the folder exists and is not empty
        if os.path.exists(folder_path) and os.listdir(folder_path):
            # Loop through each file in the directory
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    # If it's a file, delete it
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    # If it's a directory, delete it and all its contents
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')      

        # Run Server                  
        self.app.run_server(debug=debug)
