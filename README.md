# FMU Check

FMU Check is a Python Web App built on [FMPy](https://github.com/CATIA-Systems/FMPy) and [Dash](https://plotly.com/dash/) to validate [Functional Mock-up Units](https://fmi-standard.org/).

## Run FMU Check

- Clone or download the repository

- Install the dependencies

```
pip install -r requirements.txt
```

- Run the Web App in development mode

```
python app.py
```

- Run the Web App for deployment

```
gunicorn --bind 0.0.0.0:80 app:app.server
```

## Copyright and License

The code is released under the [2-Clause BSD License](https://opensource.org/licenses/BSD-2-Clause).
Copyright (C) 2024 the Modelica Association Project FMI.
