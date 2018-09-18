import os
import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

db_u = os.environ["MYSQL_USER"]
db_p = os.environ["MYSQL_PASSWORD"]
db_host = os.environ["MYSQL_HOST"]
db_db = os.environ["MYSQL_DATABASE"]

dbconn = "mysql://%s:%s@%s:3306/%s?charset=utf8mb4" % (db_u, db_p, db_host, db_db)

engine = None
engine_failure = 0
RETRY_LIMIT = 10

while not engine and engine_failure < RETRY_LIMIT:
    try:
        engine = create_engine(dbconn)
        connection = engine.connect()
        connection.execute("select 1 as result")
        connection.close()
    except Exception as e:
        print(e)
        wait_time = engine_failure * engine_failure
        engine_failure += 1
        logging.info("Database start failure %s, waiting %s" % (engine_failure, wait_time))
        time.sleep(wait_time)

Session = scoped_session(sessionmaker(bind=engine))
