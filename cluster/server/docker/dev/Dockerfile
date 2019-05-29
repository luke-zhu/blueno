FROM python:3.7
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - && apt-get install -y nodejs
WORKDIR /src
COPY ./package*.json ./
RUN npm install
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./src ./src
COPY ./public ./public
COPY ./app ./app
COPY ./cli.py ./cli.py
# Create build/index.html so flask doesn't return 500 when trying to load index.html
RUN mkdir ./build && touch ./build/index.html
ENV PORT 5000
# We need to run the create-react-app server on port 5000. Keep the flask server
# port in-sync with the "proxy" field in package.json
CMD FLASK_APP=app FLASK_ENV=development flask run --port=5001 & PORT=5000 npm run start
