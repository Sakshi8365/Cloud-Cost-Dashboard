

import os
import psycopg2
import csv
from io import StringIO
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
from pydantic import BaseModel
from contextlib import asynccontextmanager

DB_URL = os.getenv("DATABASE_URL", "postgresql://clouduser:cloudpass@timescaledb:5432/cloudcost")
MOCK_DATA: list[Dict[str, object]] = [
    {"timestamp": "2025-08-01T00:00:00Z", "service": "EC2", "cost": 12.34},
    {"timestamp": "2025-08-01T01:00:00Z", "service": "S3", "cost": 2.50},
    {"timestamp": "2025-08-01T02:00:00Z", "service": "Lambda", "cost": 0.75},
    {"timestamp": "2025-08-01T03:00:00Z", "service": "EC2", "cost": 13.10},
    {"timestamp": "2025-08-01T04:00:00Z", "service": "S3", "cost": 2.60},
    {"timestamp": "2025-08-01T05:00:00Z", "service": "Lambda", "cost": 0.80},
    {"timestamp": "2025-08-01T06:00:00Z", "service": "EC2", "cost": 14.00},
    {"timestamp": "2025-08-01T07:00:00Z", "service": "S3", "cost": 2.70},
    {"timestamp": "2025-08-01T08:00:00Z", "service": "Lambda", "cost": 0.85},
    {"timestamp": "2025-08-01T09:00:00Z", "service": "EC2", "cost": 15.00},
]



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed mock data if table exists and is empty
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.costs');")
        table_row = cur.fetchone()
        table_exists = table_row is not None and table_row[0] is not None
        if table_exists:
            cur.execute("SELECT COUNT(*) FROM costs;")
            result = cur.fetchone()
            count = result[0] if result else 0
            if count == 0:
                for row in MOCK_DATA:
                    cur.execute(
                        "INSERT INTO costs (timestamp, service, cost) VALUES (%s, %s, %s)",
                        (row["timestamp"], row["service"], row["cost"])
                    )
                conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Startup seeding error: {e}")
    yield

app = FastAPI(lifespan=lifespan)

# Endpoint to reset the database to mock data
@app.post("/reset-mock-data")
def reset_mock_data():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM costs;")
    for row in MOCK_DATA:
        cur.execute(
            "INSERT INTO costs (timestamp, service, cost) VALUES (%s, %s, %s)",
            (row["timestamp"], row["service"], row["cost"])
        )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "reset to mock data"}

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    s = StringIO(content.decode())
    reader = csv.DictReader(s)
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    # Optionally clear old data or append
    cur.execute("DELETE FROM costs;")
    for row in reader:
        cur.execute(
            "INSERT INTO costs (timestamp, service, cost) VALUES (%s, %s, %s)",
            (row["timestamp"], row["service"], float(row["cost"]))
        )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CostRecord(BaseModel):
    timestamp: str
    service: str
    cost: float

@app.get("/costs", response_model=List[CostRecord])
def get_costs(service: Optional[str] = None, limit: int = 100):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    if service:
        cur.execute("SELECT timestamp, service, cost FROM costs WHERE service=%s ORDER BY timestamp DESC LIMIT %s", (service, limit))
    else:
        cur.execute("SELECT timestamp, service, cost FROM costs ORDER BY timestamp DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [CostRecord(timestamp=str(r[0]), service=r[1], cost=float(r[2])) for r in rows]

@app.get("/")
def read_root():
    return {"message": "Cloud Cost & Performance Monitoring API is running."}
