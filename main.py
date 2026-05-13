from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from fastapi.responses import StreamingResponse
import pandas as pd
import matplotlib.pyplot as plt
import io
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API is working"}

@app.get("/tables")
def get_tables():
    try:
        query = text("SHOW TABLES")
        with engine.connect() as conn:
            result = conn.execute(query)
            tables = [list(row)[0] for row in result]
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{table_name}")
def get_table_data(table_name: str):
    try:
        query = text("SHOW TABLES")
        with engine.connect() as conn:
            result = conn.execute(query)
            tables = [list(row)[0] for row in result]

        if table_name not in tables:
            raise HTTPException(status_code=400, detail="Table not found")

        query = text(f"SELECT * FROM {table_name} LIMIT 100")
        with engine.connect() as conn:
            result = conn.execute(query)
            data = [dict(row._mapping) for row in result]

        return {"table": table_name, "count": len(data), "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/visualize/{table_name}")
def visualize_table(table_name: str):
    try:
        query = text("SHOW TABLES")
        with engine.connect() as conn:
            result = conn.execute(query)
            tables = [list(row)[0] for row in result]

        if table_name not in tables:
            raise HTTPException(status_code=400, detail="Table not found")

        query = text(f"SELECT * FROM {table_name} LIMIT 50")
        with engine.connect() as conn:
            result = conn.execute(query)
            data = [dict(row._mapping) for row in result]

        if not data:
            raise HTTPException(status_code=404, detail="No data found")

        df = pd.DataFrame(data)

        num_cols = df.select_dtypes(include=["int64", "float64"]).columns
        cat_cols = df.select_dtypes(include=["object"]).columns

        if len(num_cols) == 0 or len(cat_cols) == 0:
            raise HTTPException(status_code=400, detail="Need at least one numeric and one text column")

        y_col = next((col for col in num_cols if col.lower() != "id"), num_cols[0])
        x_col = cat_cols[0]

        df = df.sort_values(by=y_col, ascending=False).head(10)

        plt.figure(figsize=(12, 6))
        plt.barh(df[x_col], df[y_col])
        plt.xlabel(y_col)
        plt.ylabel(x_col)
        plt.title(f"{table_name}: {x_col} vs {y_col}")
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close()

        return StreamingResponse(img, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))