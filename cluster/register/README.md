This directory contains the code for the dataset registration pipelines.

When a user calls on the `/register` or `/setup` endpoint of the Blueno server, K8s jobs
are created which run the code in this directory. See `main.py` for more
information on how this program registers the data.