from flask import Flask, jsonify, request
from sqlalchemy.sql import text as sa_text
from sqlalchemy import create_engine
from joblib import Parallel, delayed
import pandas as pd
from tqdm import tqdm
import time
import json

app = Flask(__name__)


def upload_data(data: pd.DataFrame, table_name: str, mode= str) -> None:
    host="db"
    user="admin"
    password="admin"
    database="gixxer"
    engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
    batch_size = 5

    def db_update(slice_from,slice_upto, if_exists) -> None:       
        data[slice_from:slice_upto].to_sql(table_name, con=engine, index=False, if_exists= if_exists)
        return None
    try:
        if mode == "append":
            Parallel(n_jobs=1,backend ="threading")(delayed(db_update)(chunk, chunk+batch_size, "append") for chunk in tqdm(range(0, len(data), batch_size)))
            return "Data Appended"

        conn = engine.connect()
        tables = conn.execute(f"show tables;").fetchall()
        tables = [table[0] for table in tables]
        if table_name in tables:
            print("table_exists updating....")
            engine.execute(sa_text(f"truncate table {table_name}").execution_options(autocommit=True))
            Parallel(n_jobs=1,backend ="threading")(delayed(db_update)(chunk, chunk+batch_size, "append") for chunk in tqdm(range(0, len(data), batch_size)))
            return "Table Truncate, Data Uploaded"
        Parallel(n_jobs=1,backend ="threading")(delayed(db_update)(chunk, chunk+batch_size, "append") for chunk in tqdm(range(0, len(data), batch_size)))        
        
    except Exception as e:
        time.sleep(2)
        engine.execute(sa_text(f"truncate table {table_name}").execution_options(autocommit=True))
        Parallel(n_jobs=1,backend ="threading")(delayed(db_update)(chunk, chunk+batch_size, "append") for chunk in tqdm(range(0, len(data), batch_size)))
        print("table not found new table created")
        return "Table Not Found, New Table Created & Data Pushed"
    return None


@app.route('/upload', methods=["POST"])
def index():
    if request.method == 'POST':
        req = request.json
        data = req["data"]
        data = pd.DataFrame.from_dict(json.loads(data))
        table_name = req['table_name']
        mode = req['mode']

    return jsonify({"status": upload_data(data=data, table_name=table_name, mode=mode)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)