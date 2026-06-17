# 初始化与表结构
import sqlite3
import json

DB = "plant.db"

def init():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        original TEXT,
        annotated TEXT,
        detections TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# 用户操作函数
def get_user(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    if res:
        return {"id": res[0], "username": res[1], "password": res[2]}
    return None

def create_user(username, hashed_pwd):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hashed_pwd))
    conn.commit()
    conn.close()

# 识别记录操作函数
def add_record(user_id, original, annotated, detections):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        INSERT INTO records (user_id, original, annotated, detections)
        VALUES (?,?,?,?)
    ''', (user_id, original, annotated, detections))
    conn.commit()
    conn.close()

def get_records(user_id, page=1, limit=10):
    offset = (page-1)*limit
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # 查询记录
    c.execute('''
              SELECT id, original, annotated, detections, created_at
              FROM records WHERE user_id=?
              ORDER BY id DESC LIMIT ? OFFSET ?
              ''', (user_id, limit, offset))
    rows = c.fetchall()
    conn.close()

    ret = []
    for r in rows:
        # 安全解析detections JSON字符串
        try:
            det_list = json.loads(r[3]) if r[3] else []
        except (json.JSONDecodeError, TypeError):
            det_list = []

        # 计算检测数量
        count = len(det_list)

        ret.append({
            "id": r[0],
            "original_image": r[1],
            "annotated_image": r[2],
            "detections": det_list,       
            "created_at": r[4],
            "detection_count": count     
        })
    return ret

# 初始化调用
init()