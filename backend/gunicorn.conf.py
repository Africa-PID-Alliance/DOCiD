import os

workers = 4  # Number of worker processes
bind = f'0.0.0.0:{os.environ.get("FLASK_PORT", "5001")}'  # Bind address and port
timeout = 120  # Set timeout for long-running requests