import os


command = os.path.join(os.environ["LABSITE_ENV_ROOT"], 'bin/gunicorn')
pythonpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bind = '127.0.0.1:8001'
workers = 2
user = os.environ["USER"]
