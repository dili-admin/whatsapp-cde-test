accesslog = 'logs/access.log'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = 'logs/application.log'
loglevel = 'info'
capture_output = True
pidfile = 'RUNNING_PID'
bind = '0.0.0.0:5000'
workers = 10
