# 依赖注入
import io
import os
from openai import OpenAI
import uuid
from app import database as db
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form
from pydantic import BaseModel
from PIL import Image
from pathlib import Path
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import passlib.hash as pwd_context

from .inference import predict_with_image
from . import database

app = FastAPI(title="植物识别系统")

# AI 配置与客户端初始化，从环境变量读取配置
API_KEY = os.getenv("DEFAULT_API_KEY", "sk-azstqttsuabpbpazawummsirfuxljrrqxbzovgbeugnfoaip")
API_BASE = os.getenv("DEFAULT_API_BASE", "https://api.siliconflow.cn/v1")
MODEL_NAME = os.getenv("DEFAULT_MODEL", "Pro/deepseek-ai/DeepSeek-V3")

# 初始化OpenAI兼容客户端
client = OpenAI(api_key=API_KEY, base_url=API_BASE)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")))
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)))

# 配置加密密钥、算法，初始化密码哈希器
SECRET_KEY = "plant123456"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 定义用户注册、登录的请求参数格式
class UserCreate(BaseModel):
    username: str
    password: str

# 生成JWT令牌
def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

# 从请求头解析JWT令牌，提取用户ID
def get_user_id(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = data.get("sub")
        print(f"从 Token 解析出的 user_id 类型: {type(user_id_str)}, 值: {user_id_str}")

# 如果user_id_str是None，int()会报错，所以要判断
        if user_id_str is not None:
            return int(user_id_str)
        return None
    
# 捕获具体异常并打印
    except Exception as e: 
        print(f"Token 解析错误: {e}")
        return None

# 保存图片到本地
def save_img(image: Image.Image, prefix: str):
    name = f"{prefix}_{uuid.uuid4().hex[:10]}.jpg"
    path = UPLOAD_DIR / name
    image.save(path, "JPEG", quality=85)
    return f"/uploads/{name}"

# 前端页面路由
@app.get("/")
def index():
    return FileResponse(BASE_DIR/"static"/"index.html")

@app.get("/login")
def login_page():
    return FileResponse(BASE_DIR/"static"/"login.html")

# 用户认证接口
@app.post("/api/register")
async def register(user: UserCreate):
    try:
        # 检查用户名是否已存在
        existing_user = db.get_user(user.username)
        if existing_user:
            return {"code": 400, "msg": "用户名已存在，请更换用户名"}

        # 截断密码以防止bcrypt报错(最大72字节)
        password_to_hash = user.password[:72]

        # 生成哈希
        hashed = pwd_context.hash(password_to_hash)

        # 写入数据库
        db.create_user(user.username, hashed)

        # 返回成功
        return {"code": 200, "msg": "注册成功"}

    except Exception as e:
        # 任何错误都捕获并返回给前端
        print(f"注册失败: {e}")
        return {"code": 500, "msg": f"注册失败: {str(e)}"}

@app.post("/api/login")
def login(user: UserCreate, response: Response):
    u = database.get_user(user.username)
    if not u or not pwd_context.verify(user.password, u["password"]):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = create_token(u["id"])
    return {"code": 200, "token": token, "msg": "登录成功"}

# 植物识别接口
@app.post("/api/predict")
async def predict(
        request: Request,
        file: UploadFile = File(...),
        conf: float = Form(0.25) 
):
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="请登录")

    try:
        # 读取图片
        bytes_img = await file.read()
        if not bytes_img:
            raise ValueError("上传的文件为空")

        # 打开图片
        try:
            img = Image.open(io.BytesIO(bytes_img)).convert("RGB")
        except Exception as e:
            raise ValueError(f"图片格式错误，无法打开: {str(e)}")

        # 执行预测
        try:
            detections, annotated = predict_with_image(img, conf)
        except Exception as e:
            raise RuntimeError(f"模型推理失败: {str(e)}")

        # 保存图片
        ori_path = save_img(img, "ori")
        ann_path = save_img(annotated, "ann")

        # 存入数据库
        try:
            database.add_record(
                user_id=user_id,
                original=ori_path,
                annotated=ann_path,
                detections=str(detections)
            )
        except Exception as e:
            raise RuntimeError(f"数据库写入失败: {str(e)}")

        return {
            "code": 200,
            "detections": detections,
            "annotated_image": ann_path
        }

    except Exception as e:
        print(f"预测接口发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 历史记录接口
@app.get("/api/history")
def history(request: Request, page: int = 1, limit: int = 10):
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="请登录")

    # 获取原始记录
    records = database.get_records(user_id, page, limit)

    # 遍历记录，补充detection_count字段
    processed_records = []
    for record in records:
        # 将对象转为字典或直接操作字典
        # 这里假设record是字典格式，如果是SQLAlchemy对象请用record.__dict__或record.to_dict()
        r_dict = record.copy() if isinstance(record, dict) else record

        # 计算检测数量
        # 安全处理：如果 detections 存在且是列表，取长度；否则默认为0
        det_list = r_dict.get("detections", [])
        count = len(det_list) if isinstance(det_list, list) else 0

        # 添加前端需要的字段
        r_dict["detection_count"] = count

        processed_records.append(r_dict)

    # 返回处理后的数据
    return {
        "code": 200,
        "records": processed_records,
        "total": len(processed_records), 
        "limit": limit
    }

@app.post("/api/user/logout")
async def logout(request: Request):
    """
    用户退出登录接口。
    由于 JWT 是无状态的，服务端无需做复杂处理，
    只需验证请求是否合法，并返回成功状态即可。
    真正的退出逻辑由前端清除本地 Token 完成。
    """
    # 验证用户是否真的已登录
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未登录")

    # 放在其他路由之后，StaticFiles之前
@app.get("/login.html")
async def redirect_login_html():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")

@app.get("/index.html")
async def redirect_index_html():
    return RedirectResponse(url="/")

@app.get("/background.png")
async def redirect_background_png():
    from fastapi.responses import FileResponse
    png_path = BASE_DIR / "static" / "background.png"
    if png_path.exists():
        return FileResponse(png_path)
    # 如果没有该图片，返回一个 1x1 透明像素或直接返回 404
    raise HTTPException(status_code=404, detail="background.png not found")

@app.post("/api/predict/image")
async def predict_image_compat(request: Request, file: UploadFile = File(...), conf: float = 0.25):
    # 直接调用原有的 predict 函数
    return await predict(request, file, conf)

# AI科普接口
@app.post("/api/ai-explain")
async def ai_explain(request: Request):
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="请登录")

    data = await request.json()
    flower_name = data.get("flower_name", "").strip()

    if not flower_name:
        return {"explanation": "未提供植物名称，请检查输入。"}

    try:
        # 构建Prompt，要求返回Markdown格式
        prompt = f"""
        你是一个专业的植物学家助手。请用中文为用户详细介绍 '{flower_name}'。
        要求包含：分类、形态特征、生长习性、主要价值（如观赏/药用）。
        请使用 Markdown 格式排版，段落清晰，字数控制在 300 字以内。
        """

        # 调用SiliconFlow/DeepSeek-V3模型
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个知识渊博的植物学专家，回答简洁专业。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,  # 对应配置中的 DEFAULT_MAX_TOKENS
            temperature=0.7   # 对应配置中的 DEFAULT_TEMPERATURE
        )

        # 提取生成的文本
        text = response.choices[0].message.content
        return {"explanation": text}

    except Exception as e:
        print(f"AI 接口调用错误: {e}")
        # 如果API调用失败，返回一个友好的错误提示
        return {
            "explanation": f"**{flower_name}**\n\n暂无法获取详细信息，请稍后重试。\n\n错误详情: {str(e)}"
        }