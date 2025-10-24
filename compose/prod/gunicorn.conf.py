bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"


