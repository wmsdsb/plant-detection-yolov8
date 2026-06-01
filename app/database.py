import pymysql
from datetime import datetime# 导入依赖库

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "charset": "utf8mb4",
}# 定义数据库配置常量


def get_connection(db_name="plant_detection"):
    config = {**DB_CONFIG, "db": db_name}
    return pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)# 获取数据库连接


def init_db():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE IF NOT EXISTS plant_detection DEFAULT CHARACTER SET utf8mb4")
    conn.commit()
    conn.close()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS detection_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(64) NOT NULL,
                    original_image VARCHAR(500) NOT NULL,
                    annotated_image VARCHAR(500),
                    detections JSON NOT NULL,
                    detection_count INT NOT NULL DEFAULT 0,
                    INDEX idx_session (session_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        conn.commit()
    finally:
        conn.close()# 初始化数据库和表


def save_record(session_id: str, original_image: str, annotated_image: str, detections: list[dict]):
    if not detections:
        return None
    import json
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO detection_records (session_id, original_image, annotated_image, detections, detection_count) "
                "VALUES (%s, %s, %s, %s, %s)",
                (session_id, original_image, annotated_image, json.dumps(detections, ensure_ascii=False), len(detections)),
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()# 保存检测记录函数


def get_records(session_id: str, limit=20, offset=0):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, created_at, original_image, annotated_image, detections, detection_count "
                "FROM detection_records WHERE session_id = %s ORDER BY id DESC LIMIT %s OFFSET %s",
                (session_id, limit, offset),
            )
            records = cur.fetchall()
            import json
            for r in records:
                if isinstance(r["detections"], str):
                    r["detections"] = json.loads(r["detections"])
                if r["created_at"]:
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            return records
    finally:
        conn.close()# 查询会话的检测历史记录


def get_record_count(session_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM detection_records WHERE session_id = %s", (session_id,))
            return cur.fetchone()["total"]
    finally:
        conn.close()# 获取会话的记录总数
