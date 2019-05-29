import os
import random
import string
import warnings

try:
    POSTGRES_CONFIG = {
        'database': os.environ['POSTGRES_DB'],
        'user': os.environ['POSTGRES_USER'],
        'password': os.environ['POSTGRES_PASSWORD'],
        'host': os.environ['POSTGRES_HOST'],
    }
except KeyError:
    POSTGRES_CONFIG = None

REDIS_HOST = os.getenv('REDIS_HOST')

try:
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
except KeyError:
    JWT_SECRET_KEY = ''.join(random.choice(string.ascii_letters)
                             for _ in range(24))

try:
    FILESYSTEM_STORE_ROOT = os.environ['FILESYSTEM_STORE_ROOT']
    if not os.path.exists(FILESYSTEM_STORE_ROOT):
        warnings.warn(f"Path '{FILESYSTEM_STORE_ROOT}' does not exist,"
                      f" not enabling filesystem store")
        FILESYSTEM_STORE_ROOT = None
except KeyError:
    FILESYSTEM_STORE_ROOT = None

try:
    GOOGLE_APPLICATION_CREDENTIALS = os.environ[
        'GOOGLE_APPLICATION_CREDENTIALS']
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        warnings.warn(f"Path '{GOOGLE_APPLICATION_CREDENTIALS}' does not"
                      f" exist, not enabling GCS store")
        GOOGLE_APPLICATION_CREDENTIALS = None
except KeyError:
    GOOGLE_APPLICATION_CREDENTIALS = None

try:
    AZURE_STORAGE_CREDENTIALS = {
        'account_name': os.environ['AZURE_STORAGE_ACCOUNT'],
        'account_key': os.environ['AZURE_STORAGE_KEY'],
    }
except KeyError:
    AZURE_STORAGE_CREDENTIALS = None
