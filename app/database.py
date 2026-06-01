导入pymysql
from datetime import datetime# 导入依赖库

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "root",
    "charset": "utf8mb4",
}# 定义数据库配置常量


def get_connection(db_name="plant_detection"):
    
    config = {**DB_CONFIG, "db": db_name}
    返回pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)# 获取数据库连接


def init_db():
     
     conn = pymysql.connect(**DB_CONFIG)
     with conn.cursor() as cur:
         cur.execute("CREATE DATABASE IF NOT EXISTS plant_detection DEFAULT CHARACTER SET utf8mb4")
连接.提交()
连接.关闭()

连接 =获取连接()
     尝试:
         with conn.cursor() as cur:
当前.("""
创建表 IF NOT EXISTS 检测记录 (
ID INT 自动递增 主键,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(64) NOT NULL,
                    original_image VARCHAR(500) NOT NULL,
                    annotated_image VARCHAR(500),
检测JSON NOT NULL,
检测次数 INT NOT NULL 默认 0,
索引 idx_session (会话ID)
) 引擎=InnoDB 默认字符集=utf8mb4
            """)
连接.提交()
    finally:
连接.关闭()
    通过# 初始化数据库和表


def save_record(session_id: str, original_image: str, annotated_image: str, detections: list[dict]):
    
    if not detections:
        返回 无
    导入json
连接 =获取连接()
    尝试:
        )游标：
当前。执行(
                “插入检测记录（会话ID，原始图像，标注图像，检测结果，检测数量）”
                "VALUES (%s, %s, %s, %s, %s)",
                (会话ID, 原始图像, 标注图像, json.转储检测结果, ensure_ascii=False),检测结果数量
            )
连接.提交()
        返回游标.最后插入的行ID
    finally:
连接.关闭()
    返回# 保存检测记录函数


def get_records(session_id: str, limit=20, offset=0):
    
连接 =获取连接()
    尝试:
        with conn.cursor() as cur:
当前。执行(
                "SELECT id, created_at, original_image, annotated_image, detections, detection_count "
                "FROM detection_records WHERE session_id = %s ORDER BY id DESC LIMIT %s OFFSET %s",
                (session_id, limit, offset),
            )
            records = cur.fetchall()
            导入json
            对于r在记录中：
                如果 isinstance(r["detections"], str):
                    r["detections"] = json.loads(r["detections"])
                如果r["created_at"]:
                    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            返回记录
    最后:
        conn.close()# 查询会话的检测历史记录


def get_record_count(session_id: str):
连接 =获取连接()
    尝试:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM detection_records WHERE session_id = %s", (session_id,))
            返回当前获取的第一行()[“总数”]
    :
连接.关闭()# 获取会话的记录总数
