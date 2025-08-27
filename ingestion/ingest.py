

import csv
import random
import os
import psycopg2
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

SERVICES: List[str] = ["s3", "ec2", "rds", "lambda", "api-gateway"]
DB_URL: str = os.getenv("DATABASE_URL", "postgresql://clouduser:cloudpass@localhost:5432/cloudcost")

# Generate mock cost data for the last 7 days, hourly
rows: List[Dict[str, Any]] = []
now = datetime.now(timezone.utc)
for service in SERVICES:
    base_cost = random.uniform(10, 100)
    for hours_ago in range(7 * 24):
        timestamp = now - timedelta(hours=hours_ago)
        # Simulate normal cost with occasional spikes
        if random.random() < 0.02:
            cost = base_cost * random.uniform(3, 6)  # anomaly
        else:
            cost = base_cost * random.uniform(0.8, 1.2)
        rows.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S%z"),
            "service": service,
            "cost": round(cost, 2)
        })

# Write to CSV (optional, for debugging)
with open("mock_cloud_costs.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "service", "cost"])
    writer.writeheader()
    writer.writerows(rows)

# Load data into TimescaleDB/PostgreSQL
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS costs (
    timestamp TIMESTAMPTZ NOT NULL,
    service TEXT NOT NULL,
    cost DOUBLE PRECISION NOT NULL
);
""")
cur.execute("""
SELECT create_hypertable('costs', 'timestamp', if_not_exists => TRUE);
""")
conn.commit()

# Insert data
cur.execute("DELETE FROM costs;")  # Clear old data for demo
for row in rows:
    cur.execute(
        "INSERT INTO costs (timestamp, service, cost) VALUES (%s, %s, %s)",
        (row["timestamp"], row["service"], row["cost"])
    )
conn.commit()
cur.close()
conn.close()

print("Mock cloud cost data loaded into database.")
