## Development Guide

Running the server locally requires:
* MongoDB 
* Python Virtual Environment
* FastAPI

Assuming Python 3.12 is installed globally. Create a virtual environment:
```
cd <project root folder>
python -m virtualenv pyenv
```

This will create a virtual environment called pyenv. Visual Studio Code (when restarted) will automatically find (and bind all python commands) to this virtual environment. 


## Installing Required Packages
Run pip from a command prompt bound to the new virtual directory
```
pip install -r requirements.txt
```
## Server Testing
Test the server (app.py) with FastAPI. To install, activate the project virtual environment then run the command
```
pip install "fastapi[standard]
```
Run the server as follows:
```

cd <project root folder>/stories

fastapi dev app.py
```

The .env file in this folder has database names and connection URL.
