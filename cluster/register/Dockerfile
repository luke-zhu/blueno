# We use 3.6 because of some GFILE related issue w/ 3.7 and tensorflow 1.13
FROM python:3.6
WORKDIR /src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY blueno.py blueno.py
COPY main.py main.py