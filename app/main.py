import io
import base64
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pathlib import Path

from .inference import predict, predict_with_image
from . import database# 项目架构与依赖使用

app = FastAPI(title="植物类别识别系统")

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"# 上传图片存储目录
UPLOAD_DIR.mkdir(exist_ok=True)# 无则创建

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")# 提供前端页面访问
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")# 提供上传图片的http访问

# 启动时初始化数据库
@app.on_event("startup")
def startup():
    # database.init_db()
    pass


def _get_session_id(request: Request, response: Response) -> str:

    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = uuid.uuid4().hex[:16]# 生成16位id
        response.set_cookie("session_id", session_id, max_age=30 * 24 * 3600)# 有效期30天
    return session_id


def _save_image(image: Image.Image, prefix: str) -> str:

    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"# 前缀+8位唯一ID
    filepath = UPLOAD_DIR / filename
    image.save(str(filepath), format="JPEG", quality=90)# 保存图片到磁盘，格式为jpg，质量90
    return filename# 返回文件名


@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))# 访问根目录时，返回到首页


@app.post("/api/predict")
async def predict_plant(request: Request, response: Response, file: UploadFile = File(...), conf: float = 0.25):

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")# 验证上传文件是否为图片

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")# 将图片转换为rgb格式

        detections = predict(image, conf=conf)
        session_id = _get_session_id(request, response)# 调用推理函数

        if detections:
            original_filename = _save_image(image, "original")
            database.save_record(session_id, original_filename, "", detections)# 只有检测到植物时才保存

        return {"detections": detections}# 返回检测结果
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))# 异常报错


@app.post("/api/predict/image")
async def predict_plant_with_image(request: Request, response: Response, file: UploadFile = File(...), conf: float = 0.25):

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")# 验证上传文件是否为图片

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")# 将图片转换为rgb格式

        detections, annotated_img = predict_with_image(image, conf=conf)# 调用推理函数

        if detections:
            session_id = _get_session_id(request, response)
            original_filename = _save_image(image, "original")
            annotated_filename = _save_image(annotated_img, "annotated")
            database.save_record(session_id, original_filename, annotated_filename, detections)# 只有检测到目标时才保存

        buf = io.BytesIO()
        annotated_img.save(buf, format="JPEG", quality=90)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")# 将标注图转为Base64编码，返回给前端

        return {
            "detections": detections,
            "annotated_image": f"data:image/jpeg;base64,{img_b64}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history(request: Request, limit: int = Query(default=20, le=100), page: int = Query(default=1, ge=1)):

    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"total": 0, "page": page, "limit": limit, "records": []}# 获取当前用户的SessionID

    total = database.get_record_count(session_id)
    offset = (page - 1) * limit
    records = database.get_records(session_id, limit=limit, offset=offset)
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "records": records,
    }# 从数据库查询总记录数和分页记录


@app.get("/api/classes")
async def list_classes():

    from .inference import get_model
    model = get_model()
    return {"classes": model.names}#获取识别模型，返回模型支持的所有植物类别名称列表
