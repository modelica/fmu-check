import os
import sys
import pickle
import zipfile

from dash import html
import dash_bootstrap_components as dbc
from fmpy import read_model_description, supported_platforms
from fmpy.validation import validate_fmu


def process_fmu(fmu_filename):

    basename, _ = os.path.splitext(fmu_filename)
    pickle_filename = basename + '.p'
    fmu_hash = os.path.basename(basename)

    try:
        model_description = read_model_description(fmu_filename, validate=False)
    except Exception as e:
        alert = dbc.Alert(
            [html.I(className='fas fa-times me-3'), f"Failed to read model description. {e}"],
            id='alert', color='danger', className='mt-3')
        with open(pickle_filename, 'wb') as f:
            pickle.dump([alert], f)
        return

    platforms = supported_platforms(fmu_filename)

    with zipfile.ZipFile(fmu_filename, 'r') as zf:
        nl = filter(lambda n: not n.endswith('/'), zf.namelist())

    fmi_types = []

    if model_description.modelExchange:
        fmi_types.append('Model Exchange')

    if model_description.coSimulation:
        fmi_types.append('Co-Simulation')

    def na(attr):
        value = getattr(model_description, attr)
        if value:
            return value
        else:
            return html.Span('n/a', className='text-muted')

    rows = [
        dbc.Row([
            dbc.Col(html.Span("FMI Version"), width=4),
            dbc.Col(html.Span(model_description.fmiVersion), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col("FMI Type", width=4),
            dbc.Col(', '.join(fmi_types), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col("Model Name", width=4),
            dbc.Col(model_description.modelName, width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col("Platforms", width=4),
            dbc.Col(', '.join(platforms), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("Continuous States"), width=4),
            dbc.Col(html.Span(model_description.numberOfContinuousStates), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("Event Indicators"), width=4),
            dbc.Col(html.Span(model_description.numberOfEventIndicators), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("Model Variables"), width=4),
            dbc.Col(html.Span(len(model_description.modelVariables)), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("Generation Date"), width=4),
            dbc.Col(na('generationDateAndTime'), width=8)
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("Generation Tool"), width=4),
            dbc.Col(na('generationTool'), width=8)
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("Description"), width=4),
            dbc.Col(na('description'), width=8)
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("SHA256"), width=4),
            dbc.Col(html.Span(fmu_hash), width=8),
        ], className='py-1'),
        dbc.Row([
            dbc.Col(html.Span("File Size"), width=4),
            dbc.Col(html.Span(f'{os.path.getsize(fmu_filename)} bytes'), width=8),
        ], className='py-1'),
    ]

    try:
        problems = validate_fmu(fmu_filename)
    except Exception as e:
        problems = [str(e)]

    if problems:
        alert = dbc.Alert(
            [
                html.P(
                    [
                        html.I(className='fas fa-exclamation-circle me-3'),
                        f"Validation failed. {len(problems)} {'problem was' if len(problems) == 1 else 'problems were'} found:"
                    ]
                ),
                html.Ul(
                    [html.Li(problem) for problem in problems]
                )
            ],
            id='alert', color='danger', className='mt-3')
    else:
        alert = dbc.Alert([html.I(className='fas fa-check me-3'), "Validation passed. No problems found."],
                          id='alert', color='success', className='mt-3')

    variables = []

    table_header = [
        html.Thead(html.Tr([
            html.Th("Type"),
            html.Th("Name"),
            html.Th("Causality"),
            html.Th("Start", className='text-right'),
            html.Th("Unit"),
            html.Th("Description")
        ]))
    ]

    for variable in model_description.modelVariables:

        unit = variable.unit

        if unit is None and variable.declaredType is not None:
            unit = variable.declaredType.unit

        if variable.type == 'Boolean':
            color = '#c900c9'
        elif variable.type == 'Binary':
            color = '#ab0000'
        elif variable.type.startswith(('Int', 'Enum')):
            color = '#c78f00'
        elif variable.type.startswith(('Real', 'Float')):
            color = '#0000bf'
        else:  # String
            color = '#00a608'

        variables.append(
            html.Tr(
                [
                    html.Td(html.Small(variable.type, style={
                        'color': color, 'border': '1px solid ' + color, 'border-radius': '1em', 'padding': '0 0.5em 0 0.5em',
                    })),
                    html.Td(variable.name),
                    # html.Td(variable.variability),
                    html.Td(variable.causality),
                    html.Td(variable.start, className='text-right'),
                    html.Td(unit),
                    html.Td(variable.description, className='text-muted')
                ]
            )
        )

    table = dbc.Table(table_header + [html.Tbody(variables)], borderless=True, size='sm')

    tabs = dbc.Tabs(
        [
            dbc.Tab(rows, label="Model Info", className='p-4'),
            dbc.Tab(table, label="Variables", className='p-4'),
            dbc.Tab(html.Pre('\n'.join(nl)), label="Files", className='p-4'),
        ],
        id='tabs'
    )

    with open(pickle_filename, 'wb') as f:
        pickle.dump([alert, tabs], f)


if __name__ == '__main__':
    process_fmu(sys.argv[1])
