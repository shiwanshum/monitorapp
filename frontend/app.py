import sqlite3
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os

# ========================
# Database configuration
# ========================
#METRICS_DB_FILE = "metrics.db"
#DB_LOG_FILE = "events.db"

METRICS_DB_FILE = "/home/nodetree/Pictures/monitorapp/sqlite_db_data/metrics.db"
DB_LOG_FILE = "/home/nodetree/Pictures/monitorapp/sqlite_db_data/db_log.sqlite"

# ========================
# Logger
# ========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# ========================
# FastAPI app
# ========================
app = FastAPI(title="DB Monitor API")

origins = [
    "http://10.101.1.50:9090",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory and mount it
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========================
# Helpers
# ========================
def get_db_connection(db_file: str):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def format_datetime(ts: str):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
    except Exception:
        return ts

def parse_time_range(range_str: str) -> str:
    """Convert shorthand (10m, 2h, 3d) to SQLite offset string"""
    try:
        if range_str.endswith("m"):
            minutes = int(range_str[:-1])
            return f"-{minutes} minutes"
        elif range_str.endswith("h"):
            hours = int(range_str[:-1])
            return f"-{hours} hours"
        elif range_str.endswith("d"):
            days = int(range_str[:-1])
            return f"-{days} days"
        elif range_str.endswith("M"):
            months = int(range_str[:-1])
            return f"-{months} months"
        else:
            return "-1 day"
    except Exception:
        return "-1 day"

# ========================
# HTML Template Route
# ========================
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    try:
        with open("templates/new_dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard HTML file not found</h1><p>Please ensure dashboard.html is in the same directory as app.py</p>",
            status_code=404
        )

# ========================
# API Endpoints
# ========================

@app.get("/api/cluster-summary")
async def get_cluster_summary():
    """Get current cluster status summary"""
    try:
        conn = get_db_connection(METRICS_DB_FILE)
        cursor = conn.cursor()
        
        # Check if cluster_status table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cluster_status';")
        if cursor.fetchone() is None:
            conn.close()
            return JSONResponse({
                "clusters": [],
                "message": "No cluster_status table found. Please ensure monitoring data is being collected."
            })
        
        cursor.execute("""
            SELECT db_type, status, master_status, slave1_status, slave2_status, timestamp
            FROM cluster_status
            WHERE id IN (
                SELECT MAX(id) FROM cluster_status GROUP BY db_type
            )
            ORDER BY db_type
        """)
        
        clusters = []
        for row in cursor.fetchall():
            clusters.append({
                "db_type": row["db_type"],
                "status": row["status"].lower(),
                "master_status": row["master_status"].lower(),
                "slave1_status": row["slave1_status"].lower(),
                "slave2_status": row["slave2_status"].lower(),
                "timestamp": format_datetime(row["timestamp"])
            })
        
        conn.close()
        return JSONResponse({"clusters": clusters})
        
    except Exception as e:
        logger.error(f"Error in cluster-summary: {str(e)}")
        return JSONResponse({
            "clusters": [],
            "error": str(e)
        })

@app.get("/api/node-status")
async def get_node_status(range: str = Query("12h")):
    try:
        offset = parse_time_range(range)
        conn = get_db_connection(METRICS_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT db_type, role, connection_status,
                COUNT(*) as total_checks,
                SUM(CASE WHEN connection_status='up' THEN 1 ELSE 0 END) as up_count,
                MAX(timestamp) as last_check
            FROM metrics
            WHERE timestamp >= datetime('now', '{offset}')
            GROUP BY db_type, role
        """)
        
        nodes = []
        for row in cursor.fetchall():
            total = row["total_checks"]
            up_count = row["up_count"]
            nodes.append({
                "db_type": row["db_type"],
                "role": row["role"],
                "current_status": row["connection_status"].lower(),
                "uptime_percentage": round((up_count/total)*100 if total>0 else 0, 2),
                "total_checks": total,
                "up_count": up_count,
                "down_count": total-up_count,
                "last_check": format_datetime(row["last_check"])
            })
        
        conn.close()
        return JSONResponse({"nodes": nodes, "time_range": range})
        
    except Exception as e:
        logger.error(f"Error in node-status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/uptime-stats")
async def get_uptime_stats(range: str = Query("24h")):
    try:
        offset = parse_time_range(range)
        conn = get_db_connection(METRICS_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT db_type, role,
                AVG(uptime_percentage) as avg_uptime,
                MIN(uptime_percentage) as min_uptime,
                MAX(uptime_percentage) as max_uptime,
                COUNT(*) as measurement_count
            FROM metrics
            WHERE timestamp >= datetime('now', '{offset}')
            AND uptime_percentage IS NOT NULL
            GROUP BY db_type, role
        """)
        
        uptime_stats = [
            {
                "db_type": row["db_type"],
                "role": row["role"],
                "average_uptime": round(row["avg_uptime"], 2),
                "minimum_uptime": round(row["min_uptime"], 2),
                "maximum_uptime": round(row["max_uptime"], 2),
                "measurement_count": row["measurement_count"]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return JSONResponse({"uptime_statistics": uptime_stats, "time_range": range})
        
    except Exception as e:
        logger.error(f"Error in uptime-stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cluster-trend")
async def get_cluster_trend(range: str = Query("24h")):
    try:
        offset = parse_time_range(range)
        conn = get_db_connection(METRICS_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT db_type,
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour_timestamp,
                status,
                COUNT(*) as status_count
            FROM cluster_status
            WHERE timestamp >= datetime('now', '{offset}')
            GROUP BY db_type, hour_timestamp, status
            ORDER BY hour_timestamp ASC
        """)
        
        trend_data = {}
        for row in cursor.fetchall():
            db = row["db_type"]
            if db not in trend_data:
                trend_data[db] = []
            trend_data[db].append({
                "timestamp": row["hour_timestamp"],
                "status": row["status"].lower(),
                "count": row["status_count"]
            })
        
        conn.close()
        return JSONResponse({"trends": trend_data, "time_range": range})
        
    except Exception as e:
        logger.error(f"Error in cluster-trend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/replication-lag")
async def get_replication_lag(range: str = Query("24h")):
    try:
        offset = parse_time_range(range)
        conn = get_db_connection(METRICS_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT db_type, role, replication_lag_seconds, timestamp
            FROM metrics
            WHERE role IN ('slave1','slave2')
            AND timestamp >= datetime('now', '{offset}')
            AND replication_lag_seconds IS NOT NULL
            ORDER BY timestamp ASC
        """)
        
        lag_data = [
            {
                "db_type": row["db_type"],
                "role": row["role"],
                "lag_seconds": row["replication_lag_seconds"],
                "timestamp": row["timestamp"]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return JSONResponse({"replication_lag": lag_data, "time_range": range})
        
    except Exception as e:
        logger.error(f"Error in replication-lag: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/connection-timeline")
async def get_connection_timeline(range: str = Query("48h")):
    """Get connection status timeline for visualization"""
    try:
        offset = parse_time_range(range)
        conn = get_db_connection(METRICS_DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT db_type, role, connection_status,
                timestamp, strftime('%Y-%m-%d %H:00:00', timestamp) as hour_group
            FROM metrics
            WHERE timestamp >= datetime('now', '{offset}')
            ORDER BY timestamp ASC
        """)
        
        timeline_data = {}
        for row in cursor.fetchall():
            key = f"{row['db_type']}_{row['role']}"
            if key not in timeline_data:
                timeline_data[key] = []
            
            timeline_data[key].append({
                "timestamp": row["timestamp"],
                "status": row["connection_status"].lower(),
                "hour": row["hour_group"]
            })
        
        conn.close()
        return JSONResponse({"timeline": timeline_data, "time_range": range})
        
    except Exception as e:
        logger.error(f"Error in connection-timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historical-events")
async def get_historical_events(range: str = Query("72h")):
    try:
        offset = parse_time_range(range)
        conn = get_db_connection(DB_LOG_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events';")
        if cursor.fetchone() is None:
            conn.close()
            return JSONResponse({"events": [], "message": "No events table found"})

        cursor.execute(f"""
            SELECT event, severity, timestamp
            FROM events
            WHERE timestamp >= datetime('now', '{offset}')
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        events = [
            {
                "event": row["event"],
                "severity": row["severity"].lower(),
                "timestamp": format_datetime(row["timestamp"])
            }
            for row in rows
        ]
        
        conn.close()
        return JSONResponse({"events": events, "time_range": range})
        
    except Exception as e:
        logger.error(f"Error in historical-events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Database Monitoring Dashboard...")
    print("Dashboard will be available at: http://localhost:9090")
    uvicorn.run(app, host="0.0.0.0", port=9090, reload=True)