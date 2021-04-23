import base64
import hashlib
import os
import pickle
import subprocess
from pathlib import Path


import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


workdir = os.path.join(os.path.dirname(__file__), 'work')

Path(workdir).mkdir(exist_ok=True)

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css'
])

app.title = "FMU Check"

server = app.server

app.layout = dbc.Container([

    dcc.Store(id='submitted-store'),

    dcc.Store(id='finished-store'),

    dcc.Interval(id='update-interval', interval=500),

    dbc.Container(
        [
            html.H2(
                [
                    "FMU Check",
                    html.Span([html.I(className='fas fa-flask mr-2'), "beta"], className='badge badge-secondary ml-3'),
                ]
                , className='bd-title'
            ),

            html.P("Validate an FMU and get the meta information from the model description", className='bd-lead'),

            html.P(
                html.A([html.I(className='fas fa-info-circle mr-2'), "What is being checked?"], id="what-is-validated-link", style={'color': '#007bff', 'cursor': 'pointer'})
            ),

            dbc.Collapse(
                [
                    html.P("FMU Check performs a static analysis of the FMU that validates the following aspects:"),
                    html.Ul(
                        [
                            html.Li("validity of the modelDescription.xml w.r.t. the XML schema"),
                            html.Li("uniqueness and validity of the variable names"),
                            html.Li("completeness and integrity of the Model Structure"),
                            html.Li("availability of the required start values"),
                            html.Li("combinations of causality and variability"),
                            html.Li("definition of units"),
                        ]
                    ),
                    html.P("It does not check the following aspects:"),
                    html.Ul(
                        [
                            html.Li("validity of the binaries"),
                            html.Li("validity of the sources"),
                            html.Li("any non-standard files inside the FMU"),
                        ]
                    )
                ],
                id="what-is-validated-paragraph"
            ),

            dbc.InputGroup(
                [
                    dbc.Input(id='fmu-input', placeholder="Select an FMU", disabled=True),
                    dbc.InputGroupAddon(
                        dcc.Upload(dbc.Button("Select",
                                              color='primary',
                                              style={'border-top-left-radius': 0, 'border-bottom-left-radius': 0}),
                        id='fmu-upload', accept='.fmu'),
                        addon_type="append",
                    ),
                ]
            ),
        ]
    ),

    dbc.Container(
        [
            dbc.Alert(
                [
                    html.I(className="fas fa-thumbs-up mr-3"),
                    "By uploading a file you agree that it is stored and processed on our server.",
                ],
                id='disclaimer', color='info', className='mt-3', dismissable=True
            )
        ],
        id='model-info-container'
    )

])


@app.callback(
    Output("what-is-validated-paragraph", "is_open"),
    [Input("what-is-validated-link", "n_clicks")],
    [State("what-is-validated-paragraph", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [
        Output('model-info-container', 'children'),
        Output("finished-store", "data"),
    ],
    [Input('update-interval', 'n_intervals')],
    [State('submitted-store', 'data')],
)
def retrieve_output(n_intervals, fmu_hash):

    if fmu_hash is None:
        raise PreventUpdate

    pickle_file = os.path.join(workdir, fmu_hash + '.p')

    if os.path.isfile(pickle_file):
        with open(pickle_file, 'rb') as f:
            components = pickle.load(f)
        return components, fmu_hash
    else:
        return dbc.Container([dbc.Spinner(color='secondary')], className='mt-5 text-center'), None


@app.callback(
    [
        Output('fmu-input', 'value'),
        Output("submitted-store", "data"),
    ],
    [Input('fmu-upload', 'contents')],
    [State('fmu-upload', 'filename')]
)
def submit(contents, filename):

    if contents is None:
        raise PreventUpdate

    data = contents.encode('utf8').split(b';base64,')[1]
    bytes = base64.decodebytes(data)
    hash = hashlib.sha256(bytes).hexdigest()

    fmu_filename = os.path.join(workdir, hash + '.fmu')

    with open(fmu_filename, "wb") as fp:
        fp.write(bytes)

    subprocess.Popen(['python', 'process.py', fmu_filename])

    return filename, hash


@app.callback(
    Output("update-interval", "disabled"),
    [
        Input("submitted-store", "data"),
        Input("finished-store", "data")
    ],
)
def disable_interval(submitted, finished):
    return not submitted or finished == submitted


if __name__ == '__main__':
    app.run_server(debug=True)
