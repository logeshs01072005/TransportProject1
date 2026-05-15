from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from database import Base, engine

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)


# ==========================================
# HOME
# ==========================================
@app.get("/")
def home():
    return {"message": "Universal Database Search API Working"}


# ==========================================
# GET ALL TABLES
# ==========================================
@app.get("/tables")
def get_tables():
    try:
        query = text("SHOW TABLES")

        with engine.connect() as conn:
            result = conn.execute(query)
            tables = [list(row)[0] for row in result]

        return {
            "total_tables": len(tables),
            "tables": tables
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# GET COLUMNS
# ==========================================
@app.get("/columns/{table_name}")
def get_columns(table_name: str):
    try:
        query = text(f"SHOW COLUMNS FROM `{table_name}`")

        with engine.connect() as conn:
            result = conn.execute(query)
            columns = [row[0] for row in result]

        return {
            "table": table_name,
            "columns": columns
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# GET TABLE DATA
# ==========================================
@app.get("/data/{table_name}")
def get_table_data(table_name: str):
    try:
        query = text(f"SELECT * FROM `{table_name}` LIMIT 100")

        with engine.connect() as conn:
            result = conn.execute(query)
            data = [dict(row._mapping) for row in result]

        return {
            "table": table_name,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# UNIVERSAL SEARCH
# ==========================================
@app.get("/search/{keyword}")
def universal_search(keyword: str):
    try:
        final_results = {}

        # Get all tables
        with engine.connect() as conn:
            tables = [list(row)[0] for row in conn.execute(text("SHOW TABLES"))]

        # Loop through tables
        for table_name in tables:
            try:
                # Get columns
                with engine.connect() as conn:
                    columns = [
                        row[0]
                        for row in conn.execute(
                            text(f"SHOW COLUMNS FROM `{table_name}`")
                        )
                    ]

                # Build dynamic conditions
                conditions = " OR ".join([
                    f"CAST(`{col}` AS CHAR) LIKE :keyword"
                    for col in columns
                ])

                # Search query
                search_query = text(f"""
                    SELECT *
                    FROM `{table_name}`
                    WHERE {conditions}
                    LIMIT 100
                """)

                with engine.connect() as conn:
                    rows = [
                        dict(row._mapping)
                        for row in conn.execute(
                            search_query,
                            {"keyword": f"%{keyword}%"}
                        )
                    ]

                if rows:
                    final_results[table_name] = {
                        "matched_rows": len(rows),
                        "data": rows
                    }

            except Exception:
                pass

        return {
            "search_keyword": keyword,
            "matched_tables": len(final_results),
            "results": final_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# FILTER BY DATE RANGE
# today, week, month, 3months, 6months, year
# ==========================================
@app.get("/filter/{table_name}/{period}")
def filter_by_period(table_name: str, period: str):

    try:

        # Period map
        period_map = {
            "today": "CURDATE()",
            "week": "CURDATE() - INTERVAL 7 DAY",
            "month": "CURDATE() - INTERVAL 1 MONTH",
            "3months": "CURDATE() - INTERVAL 3 MONTH",
            "6months": "CURDATE() - INTERVAL 6 MONTH",
            "year": "CURDATE() - INTERVAL 1 YEAR"
        }

        # Validate period
        if period not in period_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period! Use: {list(period_map.keys())}"
            )

        # Get columns
        with engine.connect() as conn:
            columns = [
                row[0]
                for row in conn.execute(
                    text(f"SHOW COLUMNS FROM `{table_name}`")
                )
            ]

        # Find date column dynamically
        date_col = None

        for col in columns:
            if "date" in col.lower():
                date_col = col
                break

        if not date_col:
            raise HTTPException(
                status_code=400,
                detail="No date column found in this table!"
            )

        from_date = period_map[period]

        # Main query
        query = text(f"""
            SELECT *
            FROM `{table_name}`
            WHERE DATE(
                REPLACE(`{date_col}`, "'", "")
            ) >= {from_date}

            ORDER BY DATE(
                REPLACE(`{date_col}`, "'", "")
            ) DESC

            LIMIT 100
        """)

        with engine.connect() as conn:
            data = [
                dict(row._mapping)
                for row in conn.execute(query)
            ]

        return {
            "table": table_name,
            "period": period,
            "date_column": date_col,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# FILTER BY DATE + KEYWORD
# ==========================================
@app.get("/filter/{table_name}/{period}/{keyword}")
def filter_by_period_and_keyword(
    table_name: str,
    period: str,
    keyword: str
):

    try:

        # Period map
        period_map = {
            "today": "CURDATE()",
            "week": "CURDATE() - INTERVAL 7 DAY",
            "month": "CURDATE() - INTERVAL 1 MONTH",
            "3months": "CURDATE() - INTERVAL 3 MONTH",
            "6months": "CURDATE() - INTERVAL 6 MONTH",
            "year": "CURDATE() - INTERVAL 1 YEAR"
        }

        # Validate period
        if period not in period_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period! Use: {list(period_map.keys())}"
            )

        # Get columns
        with engine.connect() as conn:
            columns = [
                row[0]
                for row in conn.execute(
                    text(f"SHOW COLUMNS FROM `{table_name}`")
                )
            ]

        # Find date column
        date_col = None

        for col in columns:
            if "date" in col.lower():
                date_col = col
                break

        if not date_col:
            raise HTTPException(
                status_code=400,
                detail="No date column found!"
            )

        from_date = period_map[period]

        # Search conditions
        conditions = " OR ".join([
            f"CAST(`{col}` AS CHAR) LIKE :keyword"
            for col in columns
        ])

        # Main query
        query = text(f"""
            SELECT *
            FROM `{table_name}`

            WHERE (
                {conditions}
            )

            AND DATE(
                REPLACE(`{date_col}`, "'", "")
            ) >= {from_date}

            ORDER BY DATE(
                REPLACE(`{date_col}`, "'", "")
            ) DESC

            LIMIT 100
        """)

        with engine.connect() as conn:
            data = [
                dict(row._mapping)
                for row in conn.execute(
                    query,
                    {"keyword": f"%{keyword}%"}
                )
            ]

        return {
            "table": table_name,
            "period": period,
            "keyword": keyword,
            "date_column": date_col,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))