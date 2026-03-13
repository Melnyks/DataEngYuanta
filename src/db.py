import os
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

def get_engine():
    # Read from environment variables
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5433")
    user = os.environ.get("DB_USER", "user")
    password = os.environ.get("DB_PASS", "password")
    dbname = os.environ.get("DB_NAME", "brokerage")

    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_engine(connection_string)

    # Retry connection
    retries = 5
    while retries > 0:
        try:
            with engine.connect() as conn:
                print("Successfully connected to the database.")
                return engine
        except OperationalError:
            print(f"Database not ready. Retrying in 5 seconds... ({retries} retries left)")
            time.sleep(5)
            retries -= 1
            
    raise Exception("Could not connect to the database after 5 retries.")