# Keep in sync with dev
FROM node:10
WORKDIR /ui
COPY ./package*.json ./
RUN npm install
COPY ./public ./public
COPY ./src ./src
RUN npm run build

FROM python:3.7
WORKDIR /server
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY ./app/ ./app/
COPY ./cli.py ./cli.py
# Copies the build/ dir from the previous step.
COPY --from=0 /ui/build/ ./build
ENV PORT 5000
CMD gunicorn --workers=3 --worker-class=gevent --access-logfile -  app:app
