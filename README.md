# distributed-systems-2024
 
## Set up guide:

IGNORE these for the time being, we don't use virtualenv or invokes yet


If you are using Unix-style operating system, you might have to replace all the "python" parts of the invoke commands to "python3" in the tasks.py file.


You can have virtualenv installed by using pip install virtualenv. This might make easier to remove unnecessary
dependencies after testing my application.


If you are using virtualenv, first use the command 
```bash
virtualenv venv
```
to create a virtual environment.


Start the virtual environment use 
```bash
source venv/Scripts/activate
```
or
```bash
source venv/bin/activate
```

Inside virtualenv or normally use 
```bash
pip install -r requirements.txt
```
to install dependencies

Inside virtualenv, to update requirements.txt after installing packages, use 
```bash
pip freeze -l > requirements.txt 
```

To start the application, use
```bash
invoke start
```

To leave virtualenv, use 
```bash
deactivate
```
