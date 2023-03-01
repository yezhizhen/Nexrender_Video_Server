# Overview
This project hosts a web server which uses [Nexrender](https://github.com/inlife/nexrender) and Adobe After Effects(**AE**) to generate videos dynamically upon receiving JSON and CSV, based on existing template.

# API
A web server handling POST request, making videos and then post a link to another server to notify the link.

# File Server
Serve files upon GET request. Only allow ips from constants/my_constants.py to interact.

# my_constants.py
Defining allowed ips, and username/password.

# how to run
## File Server
```python
cd "File Server"
python file_server.py
```