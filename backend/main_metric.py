import os
import datetime
import logging
import sqlite3
import psycopg2
import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from db_config import DB_CONFIG  # Import your DB configuration

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DB_LOG_DIR = "monitorapp/sqlite_db_data"
os.makedirs(DB_LOG_DIR, exist_ok=True)

# Path to store the metrics database
METRICS_DB_FILE = "/home/nodetree/Pictures/monitorapp/sqlite_db_data/metrics.db"
DB_LOG_FILE = "/home/nodetree/Pictures/monitorapp/sqlite_db_data/db_log.sqlite"

# Global scheduler
scheduler = BackgroundScheduler()


# ======================= Helper functions =======================

def format_timestamps(obj):
    if isinstance(obj, dict):
        return {k: format_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [format_timestamps(item) for item in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, str):
        try:
            dt = datetime.datetime.fromisoformat(obj.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return obj
    else:
        return obj


def init_metrics_db():
    conn = sqlite3.connect(METRICS_DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            db_type TEXT NOT NULL,
            role TEXT NOT NULL,
            host TEXT,
            port INTEGER,
            connection_status TEXT NOT NULL,
            cluster_version TEXT,
            cluster_creation_timestamp TEXT,
            replication_lag_seconds REAL,
            replication_io_running TEXT,
            replication_sql_running TEXT,
            uptime_percentage REAL,
            last_node_down_time TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cluster_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            db_type TEXT NOT NULL,
            status TEXT NOT NULL,
            master_status TEXT,
            slave1_status TEXT,
            slave2_status TEXT
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cluster_timestamp ON cluster_status(timestamp);")
    conn.commit()
    conn.close()


def init_logging_db():
    conn = sqlite3.connect(DB_LOG_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS status_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            db_type TEXT,
            role TEXT,
            host TEXT,
            status TEXT
        );
    """)
    conn.commit()
    conn.close()


def log_status(db_type, role, host, status):
    conn = sqlite3.connect(DB_LOG_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO status_logs (db_type, role, host, status)
        VALUES (?, ?, ?, ?)
    """, (db_type, role, host, status))
    conn.commit()
    conn.close()


def save_metrics_to_db(db_type, role, host, port, metrics, uptime_data):
    conn = sqlite3.connect(METRICS_DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO metrics (
            db_type, role, host, port, connection_status, cluster_version,
            cluster_creation_timestamp, replication_lag_seconds, replication_io_running,
            replication_sql_running, uptime_percentage, last_node_down_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        db_type, role, host, port, metrics["connection_status"],
        metrics["cluster_version"], metrics["cluster_creation_timestamp"],
        metrics.get("replication_lag_seconds"), metrics.get("replication_io_running"),
        metrics.get("replication_sql_running"),
        float(uptime_data["uptime_percentage"].replace('%', '')) if uptime_data["uptime_percentage"] != "No data" else None,
        uptime_data["last_node_down_time"]
    ))
    conn.commit()
    conn.close()


def save_cluster_status_to_db(db_type, status, master_status, slave1_status, slave2_status):
    conn = sqlite3.connect(METRICS_DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO cluster_status (db_type, status, master_status, slave1_status, slave2_status)
        VALUES (?, ?, ?, ?, ?)
    """, (db_type, status, master_status, slave1_status, slave2_status))
    conn.commit()
    conn.close()


def calculate_uptime(db_type, role):
    conn = sqlite3.connect(DB_LOG_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, status FROM status_logs
        WHERE db_type = ? AND role = ?
        ORDER BY timestamp DESC
        LIMIT 1000
    """, (db_type, role))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"uptime_percentage": "No data", "last_node_down_time": "No data"}

    total = len(rows)
    up = sum(1 for r in rows if r[1] == "up")
    last_down_time = next((r[0] for r in rows if r[1] == "down"), "Never")
    return {
        "uptime_percentage": f"{(up / total) * 100:.2f}%",
        "last_node_down_time": last_down_time
    }


def get_db_metrics(db_type, role, db_config):
    host, port, user, password, dbname = None, None, None, None, None

    # Assign DB config
    if db_type == "postgres":
        if role == "master":
            host, port, user, password, dbname = db_config["PG_MASTER_IP"], db_config["PG_MASTER_PORT"], db_config["PG_USER"], db_config["PG_PASS"], db_config["PG_DB_NAME"]
        elif role == "slave1":
            host, port, user, password, dbname = db_config["PG_SLAVE1_IP"], db_config["PG_SLAVE1_PORT"], db_config["PG_USER"], db_config["PG_PASS"], db_config["PG_DB_NAME"]
        elif role == "slave2":
            host, port, user, password, dbname = db_config["PG_SLAVE2_IP"], db_config["PG_SLAVE2_PORT"], db_config["PG_SLAVE2_USER"], db_config["PG_SLAVE2_PASS"], db_config["PG_SLAVE2_DB_NAME"]

    elif db_type == "mysql":
        if role == "master":
            host, port, user, password, dbname = db_config["MYSQL_MASTER_IP"], db_config["MYSQL_MASTER_PORT"], db_config["MYSQL_USER"], db_config["MYSQL_PASS"], db_config["MYSQL_DB_NAME"]
        elif role == "slave1":
            host, port, user, password, dbname = db_config["MYSQL_SLAVE1_IP"], db_config["MYSQL_SLAVE1_PORT"], db_config["MYSQL_USER"], db_config["MYSQL_PASS"], db_config["MYSQL_DB_NAME"]
        elif role == "slave2":
            host, port, user, password, dbname = db_config["MYSQL_SLAVE2_IP"], db_config["MYSQL_SLAVE2_PORT"], db_config["MYSQL_SLAVE2_USER"], db_config["MYSQL_SLAVE2_PASS"], db_config["MYSQL_SLAVE2_DB_NAME"]

    metrics = {"connection_status": "down", "cluster_version": "N/A", "cluster_creation_timestamp": "N/A"}

    try:
        if db_type == "postgres":
            conn = psycopg2.connect(
                host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=5
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                metrics["cluster_version"] = cur.fetchone()[0]
                cur.execute("SELECT pg_postmaster_start_time();")
                metrics["cluster_creation_timestamp"] = cur.fetchone()[0].isoformat()
                if role in ["slave1", "slave2"]:
                    cur.execute("SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;")
                    lag = cur.fetchone()[0]
                    metrics["replication_lag_seconds"] = lag.total_seconds() if lag else None
            conn.close()
            metrics["connection_status"] = "up"

        elif db_type == "mysql":
            conn = mysql.connector.connect(
                host=host, port=port, user=user, password=password, database=dbname, connection_timeout=5
            )
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT VERSION() AS version;")
            row = cur.fetchone()
            metrics["cluster_version"] = row["version"] if row else "N/A"
            cur.execute("SHOW GLOBAL STATUS LIKE 'Uptime';")
            row2 = cur.fetchone()
            if row2 and "Value" in row2:
                uptime_seconds = int(row2["Value"])
                start_time = datetime.datetime.now() - datetime.timedelta(seconds=uptime_seconds)
                metrics["cluster_creation_timestamp"] = start_time.isoformat() + "Z"
            if role in ["slave1", "slave2"]:
                cur.execute("SHOW SLAVE STATUS;")
                slave_status = cur.fetchone()
                if slave_status:
                    metrics["replication_lag_seconds"] = slave_status.get("Seconds_Behind_Master", None)
                    metrics["replication_io_running"] = slave_status.get("Slave_IO_Running", None)
                    metrics["replication_sql_running"] = slave_status.get("Slave_SQL_Running", None)
            cur.close()
            conn.close()
            metrics["connection_status"] = "up"

    except Exception as e:
        logger.error(f"Error connecting to {db_type} at {host}:{port}: {e}")
        metrics["connection_status"] = "down"

    log_status(db_type, role, host, metrics["connection_status"])
    return metrics, host, port


def get_status_summary(master_status, slave1_status, slave2_status):
    if master_status == "up" and slave1_status == "up" and slave2_status == "up":
        return "healthy"
    elif master_status == "down":
        return "critical"
    elif slave1_status == "down" or slave2_status == "down":
        return "degraded"
    else:
        return "unknown"


def poll_and_save_metrics():
    """Poll database metrics and save"""
    try:
        logger.info("Collecting metrics...")
        init_logging_db()
        databases = [
            ("postgres", "master"), ("postgres", "slave1"), ("postgres", "slave2"),
            ("mysql", "master"), ("mysql", "slave1"), ("mysql", "slave2")
        ]
        pg_statuses, mysql_statuses = {}, {}
        for db_type, role in databases:
            metrics, host, port = get_db_metrics(db_type, role, DB_CONFIG)
            uptime_data = calculate_uptime(db_type, role)
            save_metrics_to_db(db_type, role, host, port, metrics, uptime_data)
            if db_type == "postgres": pg_statuses[role] = metrics["connection_status"]
            else: mysql_statuses[role] = metrics["connection_status"]

        pg_cluster_status = get_status_summary(pg_statuses.get("master", "down"),
                                               pg_statuses.get("slave1", "down"),
                                               pg_statuses.get("slave2", "down"))
        save_cluster_status_to_db("postgres", pg_cluster_status,
                                  pg_statuses.get("master", "down"),
                                  pg_statuses.get("slave1", "down"),
                                  pg_statuses.get("slave2", "down"))

        mysql_cluster_status = get_status_summary(mysql_statuses.get("master", "down"),
                                                  mysql_statuses.get("slave1", "down"),
                                                  mysql_statuses.get("slave2", "down"))
        save_cluster_status_to_db("mysql", mysql_cluster_status,
                                  mysql_statuses.get("master", "down"),
                                  mysql_statuses.get("slave1", "down"),
                                  mysql_statuses.get("slave2", "down"))
        logger.info("Metrics collection complete")

    except Exception as e:
        logger.error(f"Error during metrics collection: {e}")


# ======================= Flask Routes =======================

@app.route("/metrics", methods=["GET"])
def get_metrics():
    init_logging_db()
    pg_master_metrics, _, _ = get_db_metrics("postgres", "master", DB_CONFIG)
    pg_slave1_metrics, _, _ = get_db_metrics("postgres", "slave1", DB_CONFIG)
    pg_slave2_metrics, _, _ = get_db_metrics("postgres", "slave2", DB_CONFIG)
    mysql_master_metrics, _, _ = get_db_metrics("mysql", "master", DB_CONFIG)
    mysql_slave1_metrics, _, _ = get_db_metrics("mysql", "slave1", DB_CONFIG)
    mysql_slave2_metrics, _, _ = get_db_metrics("mysql", "slave2", DB_CONFIG)

    pg_cluster_status = get_status_summary(pg_master_metrics["connection_status"],
                                           pg_slave1_metrics["connection_status"],
                                           pg_slave2_metrics["connection_status"])
    mysql_cluster_status = get_status_summary(mysql_master_metrics["connection_status"],
                                              mysql_slave1_metrics["connection_status"],
                                              mysql_slave2_metrics["connection_status"])

    pg_master_uptime = calculate_uptime("postgres", "master")
    pg_slave1_uptime = calculate_uptime("postgres", "slave1")
    pg_slave2_uptime = calculate_uptime("postgres", "slave2")
    mysql_master_uptime = calculate_uptime("mysql", "master")
    mysql_slave1_uptime = calculate_uptime("mysql", "slave1")
    mysql_slave2_uptime = calculate_uptime("mysql", "slave2")

    response = {
        "postgres_cluster": {
            "status": pg_cluster_status,
            "master_node": {**pg_master_metrics, **pg_master_uptime},
            "slave1_node": {**pg_slave1_metrics, **pg_slave1_uptime},
            "slave2_node": {**pg_slave2_metrics, **pg_slave2_uptime},
        },
        "mysql_cluster": {
            "status": mysql_cluster_status,
            "master_node": {**mysql_master_metrics, **mysql_master_uptime},
            "slave1_node": {**mysql_slave1_metrics, **mysql_slave1_uptime},
            "slave2_node": {**mysql_slave2_metrics, **mysql_slave2_uptime},
        }
    }
    return jsonify(format_timestamps(response))


@app.route("/metrics/history", methods=["GET"])
def get_metrics_history():
    hours = int(request.args.get("hours", 24))
    db_type = request.args.get("db_type")
    role = request.args.get("role")

    conn = sqlite3.connect(METRICS_DB_FILE)
    cur = conn.cursor()
    query = f"SELECT * FROM metrics WHERE timestamp >= datetime('now', '-{hours} hours')"
    params = []
    if db_type:
        query += " AND db_type = ?"
        params.append(db_type)
    if role:
        query += " AND role = ?"
        params.append(role)
    query += " ORDER BY timestamp DESC"
    cur.execute(query, params)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    conn.close()

    metrics_history = [dict(zip(columns, row)) for row in rows]
    return jsonify(format_timestamps({
        "total_records": len(metrics_history),
        "time_range_hours": hours,
        "filters": {"db_type": db_type, "role": role},
        "metrics": metrics_history
    }))


@app.route("/cluster/history", methods=["GET"])
def get_cluster_history():
    hours = int(request.args.get("hours", 24))
    db_type = request.args.get("db_type")

    conn = sqlite3.connect(METRICS_DB_FILE)
    cur = conn.cursor()
    query = f"SELECT * FROM cluster_status WHERE timestamp >= datetime('now', '-{hours} hours')"
    params = []
    if db_type:
        query += " AND db_type = ?"
        params.append(db_type)
    query += " ORDER BY timestamp DESC"
    cur.execute(query, params)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    conn.close()

    cluster_history = [dict(zip(columns, row)) for row in rows]
    return jsonify(format_timestamps({
        "total_records": len(cluster_history),
        "time_range_hours": hours,
        "filters": {"db_type": db_type},
        "cluster_status_history": cluster_history
    }))


@app.route("/metrics/collect", methods=["POST"])
def manual_collect_metrics():
    try:
        poll_and_save_metrics()
        return jsonify({
            "status": "success",
            "message": "Metrics collection completed successfully",
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Manual metrics collection failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Metrics collection failed: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }), 500


# ======================= Scheduler =======================

def start_scheduler():
    init_logging_db()
    init_metrics_db()

    # ⬇️ POLLING INTERVAL CONFIGURATION  
    # For testing: run every 10 minutes  
    # For production: change minutes=10 → hours=1 (or as needed)
    scheduler.add_job(
        func=poll_and_save_metrics,
        trigger=IntervalTrigger(minutes=10),  # <-- change minutes=10 to hours=1 in production
        id='metrics_collection',
        name='Collect DB metrics periodically',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")


# ======================= Main =======================

if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=5000, debug=True)
