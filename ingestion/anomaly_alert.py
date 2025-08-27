import os
import psycopg2
# smtplib import removed (unused)
    # from email.mime.text import MIMEText  # Unused import removed


DB_URL = os.getenv("DATABASE_URL", "postgresql://clouduser:cloudpass@localhost:5432/cloudcost")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")  # Set this in your environment
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")  # Set this in your environment
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")  # Set this in your environment

# --- Anomaly Detection ---
from typing import List, Tuple, Any, DefaultDict, TypedDict
class SendGridContent(TypedDict):
    type: str
    value: str

class SendGridPersonalization(TypedDict):
    to: List[dict[str, str]]

class SendGridPayload(TypedDict):
    personalizations: List[SendGridPersonalization]
    from_: dict[str, str]
    subject: str
    content: List[SendGridContent]

def detect_anomalies() -> List[Tuple[str, Any, float, float]]:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    # Get last 7 days of cost data per service
    cur.execute("""
        SELECT service, date_trunc('hour', timestamp) as hour, SUM(cost) as total_cost
        FROM costs
        WHERE timestamp > NOW() - INTERVAL '7 days'
        GROUP BY service, hour
        ORDER BY service, hour
    """)
    rows = cur.fetchall()
    # Organize by service
    from collections import defaultdict
    import statistics
    service_costs: DefaultDict[str, List[Tuple[Any, float]]] = defaultdict(list)
    for service, hour, total_cost in rows:
        service_costs[service].append((hour, total_cost))
    alerts: List[Tuple[str, Any, float, float]] = []
    for service, data in service_costs.items():
        costs = [c for _, c in data]
        if len(costs) < 10:
            continue  # Not enough data
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs)
        threshold = mean + 3 * stdev
        for hour, cost in data[-24:]:  # Check last 24 hours
            if cost > threshold:
                alerts.append((str(service), hour, float(cost), float(threshold)))
    cur.close()
    conn.close()
    return alerts

# --- Alerting (Slack) ---
def send_slack_alert(service: str, hour: Any, cost: float, threshold: float) -> None:
    import requests
    if not SLACK_WEBHOOK_URL:
        print("No Slack webhook set.")
        return
    msg = f"Anomaly detected for {service} at {hour}: cost ${cost:.2f} (threshold ${threshold:.2f})"
    requests.post(SLACK_WEBHOOK_URL, json={"text": msg})

# --- Alerting (Email via SendGrid) ---
def send_email_alert(service: str, hour: Any, cost: float, threshold: float) -> None:
    if not SENDGRID_API_KEY or not ALERT_EMAIL:
        print("No SendGrid API key or alert email set.")
        return
    import requests
    msg = f"Anomaly detected for {service} at {hour}: cost ${cost:.2f} (threshold ${threshold:.2f})"
    data: SendGridPayload = {
        "personalizations": [{"to": [{"email": ALERT_EMAIL}]}],
        "from_": {"email": ALERT_EMAIL},
        "subject": "Cloud Cost Anomaly Alert",
        "content": [{"type": "text/plain", "value": msg}]
    }
    # SendGrid expects 'from', not 'from_'. Fix key before sending.
    data_to_send = dict(data)
    data_to_send["from"] = data_to_send.pop("from_", {"email": ALERT_EMAIL})
    requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
        json=data_to_send
    )

if __name__ == "__main__":
    alerts = detect_anomalies()
    for service, hour, cost, threshold in alerts:
        print(f"ALERT: {service} at {hour}: cost ${cost:.2f} (threshold ${threshold:.2f})")
        send_slack_alert(service, hour, cost, threshold)
        send_email_alert(service, hour, cost, threshold)
    if not alerts:
        print("No anomalies detected.")
