from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from database import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Universal Database Search API Working"}

@app.get("/tables")
def get_tables():
    try:
        query = text("SHOW TABLES")
        with engine.connect() as conn:
            result = conn.execute(query)
            tables = [list(row)[0] for row in result]
        return {"total_tables": len(tables), "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/columns/{table_name}")
def get_columns(table_name: str):
    try:
        query = text(f"SHOW COLUMNS FROM `{table_name}`")
        with engine.connect() as conn:
            result = conn.execute(query)
            columns = [row[0] for row in result]
        return {"table": table_name, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{table_name}")
def get_table_data(table_name: str):
    try:
        query = text(f"SELECT * FROM `{table_name}` LIMIT 100")
        with engine.connect() as conn:
            result = conn.execute(query)
            data = [dict(row._mapping) for row in result]
        return {"table": table_name, "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/{keyword}")
def universal_search(keyword: str):
    try:
        final_results = {}
        with engine.connect() as conn:
            tables = [list(row)[0] for row in conn.execute(text("SHOW TABLES"))]
        for table_name in tables:
            try:
                with engine.connect() as conn:
                    columns = [row[0] for row in conn.execute(text(f"SHOW COLUMNS FROM `{table_name}`"))]
                conditions = " OR ".join([f"CAST(`{col}` AS CHAR) LIKE :keyword" for col in columns])
                search_query = text(f"SELECT * FROM `{table_name}` WHERE {conditions} LIMIT 100")
                with engine.connect() as conn:
                    rows = [dict(row._mapping) for row in conn.execute(search_query, {"keyword": f"%{keyword}%"})]
                if rows:
                    final_results[table_name] = {"matched_rows": len(rows), "data": rows}
            except Exception:
                pass
        return {"search_keyword": keyword, "matched_tables": len(final_results), "results": final_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))