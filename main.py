from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from database import Base, engine

# ==========================================
# FASTAPI APP
# ==========================================
app = FastAPI()

# ==========================================
# CREATE TABLES
# ==========================================
Base.metadata.create_all(bind=engine)


# ==========================================
# HOME API
# ==========================================
@app.get("/")
def home():

    return {
        "message": "Universal Database Search API Working"
    }


# ==========================================
# GET ALL TABLES
# ==========================================
@app.get("/tables")
def get_tables():

    try:

        query = text("SHOW TABLES")

        with engine.connect() as conn:

            result = conn.execute(query)

            tables = []

            for row in result:

                tables.append(list(row)[0])

        return {
            "total_tables": len(tables),
            "tables": tables
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# GET TABLE COLUMNS
# ==========================================
@app.get("/columns/{table_name}")
def get_columns(table_name: str):

    try:

        query = text(
            f"SHOW COLUMNS FROM `{table_name}`"
        )

        with engine.connect() as conn:

            result = conn.execute(query)

            columns = []

            for row in result:

                columns.append(row[0])

        return {
            "table": table_name,
            "columns": columns
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# GET TABLE DATA
# ==========================================
@app.get("/data/{table_name}")
def get_table_data(table_name: str):

    try:

        query = text(f"""
            SELECT *
            FROM `{table_name}`
            LIMIT 100
        """)

        with engine.connect() as conn:

            result = conn.execute(query)

            data = []

            for row in result:

                data.append(dict(row._mapping))

        return {
            "table": table_name,
            "count": len(data),
            "data": data
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# UNIVERSAL SEARCH
# ==========================================
@app.get("/search/{keyword}")
def universal_search(keyword: str):

    try:

        final_results = {}

        # ==================================
        # GET ALL TABLES
        # ==================================
        table_query = text("SHOW TABLES")

        with engine.connect() as conn:

            result = conn.execute(table_query)

            tables = []

            for row in result:

                tables.append(list(row)[0])

        # ==================================
        # LOOP TABLES
        # ==================================
        for table_name in tables:

            try:

                # ==========================
                # GET COLUMNS
                # ==========================
                column_query = text(
                    f"SHOW COLUMNS FROM `{table_name}`"
                )

                with engine.connect() as conn:

                    result = conn.execute(column_query)

                    columns = []

                    for row in result:

                        columns.append(row[0])

                # ==========================
                # CREATE CONDITIONS
                # ==========================
                conditions = []

                for col in columns:

                    conditions.append(
                        f"CAST(`{col}` AS CHAR) LIKE :keyword"
                    )

                where_clause = " OR ".join(conditions)

                # ==========================
                # SEARCH QUERY
                # ==========================
                search_query = text(f"""
                    SELECT *
                    FROM `{table_name}`
                    WHERE {where_clause}
                    LIMIT 100
                """)

                with engine.connect() as conn:

                    result = conn.execute(
                        search_query,
                        {
                            "keyword": f"%{keyword}%"
                        }
                    )

                    rows = []

                    for row in result:

                        rows.append(dict(row._mapping))

                # ==========================
                # STORE RESULTS
                # ==========================
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

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# COMPANY / BRANCH + LAST DAYS
# ==========================================
@app.get("/company-last-days/{table_name}/{company_name}/{days}")
def company_last_days(
    table_name: str,
    company_name: str,
    days: int
):

    try:

        # ==================================
        # GET COLUMNS
        # ==================================
        column_query = text(
            f"SHOW COLUMNS FROM `{table_name}`"
        )

        with engine.connect() as conn:

            result = conn.execute(column_query)

            columns = []

            for row in result:

                columns.append(row[0])

        # ==================================
        # CREATE SEARCH CONDITIONS
        # ==================================
        conditions = []

        for col in columns:

            if col.lower() != "date":

                conditions.append(
                    f"CAST(`{col}` AS CHAR) LIKE :company_name"
                )

        where_clause = " OR ".join(conditions)

        # ==================================
        # FINAL QUERY
        # ==================================
        query = text(f"""
            SELECT *
            FROM `{table_name}`
            WHERE (
                {where_clause}
            )
            AND DATE(
                REPLACE(date, "'", "")
            ) >= CURDATE() - INTERVAL :days DAY
            ORDER BY id DESC
        """)

        with engine.connect() as conn:

            result = conn.execute(
                query,
                {
                    "company_name": f"%{company_name}%",
                    "days": days
                }
            )

            data = []

            for row in result:

                data.append(dict(row._mapping))

        return {
            "table": table_name,
            "company_name": company_name,
            "last_days": days,
            "count": len(data),
            "data": data
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# COMPANY / BRANCH + LAST MONTHS
# ==========================================
@app.get("/company-last-months/{table_name}/{company_name}/{months}")
def company_last_months(
    table_name: str,
    company_name: str,
    months: int
):

    try:

        # ==================================
        # GET COLUMNS
        # ==================================
        column_query = text(
            f"SHOW COLUMNS FROM `{table_name}`"
        )

        with engine.connect() as conn:

            result = conn.execute(column_query)

            columns = []

            for row in result:

                columns.append(row[0])

        # ==================================
        # CREATE SEARCH CONDITIONS
        # ==================================
        conditions = []

        for col in columns:

            if col.lower() != "date":

                conditions.append(
                    f"CAST(`{col}` AS CHAR) LIKE :company_name"
                )

        where_clause = " OR ".join(conditions)

        # ==================================
        # FINAL QUERY
        # ==================================
        query = text(f"""
            SELECT *
            FROM `{table_name}`
            WHERE (
                {where_clause}
            )
            AND DATE(
                REPLACE(date, "'", "")
            ) >= CURDATE() - INTERVAL :months MONTH
            ORDER BY id DESC
        """)

        with engine.connect() as conn:

            result = conn.execute(
                query,
                {
                    "company_name": f"%{company_name}%",
                    "months": months
                }
            )

            data = []

            for row in result:

                data.append(dict(row._mapping))

        return {
            "table": table_name,
            "company_name": company_name,
            "last_months": months,
            "count": len(data),
            "data": data
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )