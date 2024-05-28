# API's for Credit Policy, Segmentation and Decision

# Prerequisites
> Python 3.6 +

# Deployment

1. Unzip the Python Code
2. python3 -m pip install virtualenv
3. virtualenv venv
4. source venv/bin/activate
5. pip install -r requirements.txt

## RUN using below command

gunicorn --bind 0.0.0.0:5001 -c gunicorn_config.py wsgi:app --workers 5

# Endpoints

For Decision Module: http://hostname:5000/decision_module
