FROM python:3
RUN pip install mlflow==0.9.0 \
    google-cloud-storage==1.14.0 \
    SQLAlchemy==1.3.1 \
    psycopg2==2.7.7
CMD mlflow server \
    --backend-store-uri postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:5432/$MLFLOW_DBNAME \
    --default-artifact-root $MLFLOW_ARTIFACT_ROOT \
    --host 0.0.0.0