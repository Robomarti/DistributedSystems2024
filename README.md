# distributed-systems-2024
 
## Set up guide:


Please use the latest release version on your reviews and issues. The documentation in here is the most up to date, so please use the documentation on this github.


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

inside virtualenv or normally use 
```bash
pip install -r requirements.txt
```
to install dependencies


To start the application, use
```bash
invoke start
```

To leave virtualenv, use 
```bash
deactivate
```