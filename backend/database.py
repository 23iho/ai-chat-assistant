from sqlalchemy import create_engine,Column,Integer,String,Text,DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
load_dotenv()
#mysql数据库连接地址
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
sql_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
#创建数据库引擎
engine = create_engine(
    sql_url,
    echo=True,  # 打印SQL语句
)
#创建基类
Base = declarative_base()
#创建会话工厂
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

#创建密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class User(Base):
    __tablename__ = "users"  #指定表名

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50),unique=True,nullable=False,index=True)
    password_hash = Column(String(255),nullable=False)
    email = Column(String(100),unique=True,nullable=True)
    create_time = Column(DateTime,default=datetime.now)

#密码加密与验证
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
#用户查询与注册
def get_user_by_username(db,username: str):
    return db.query(User).filter(User.username == username).first()
def create_user(db,username:str,password:str,email:str = None):
    hashed_password  = get_password_hash(password)
    db_user = User(
        username=username,
        password_hash=hashed_password,
        email=email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

#聊天记录表模型
class ChatRecord(Base):
    __tablename__ = "chat_records"  #指定表名

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    role = Column(String(20),nullable=False)  # "user" 或 "assistant"
    content = Column(Text,nullable=False)
    create_time = Column(DateTime,default=datetime.now)

#自动创建表
Base.metadata.create_all(bind=engine)

#获取数据库连接
def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_and_record(db, user_id: int, role: str, content: str):
    """
    保存单条聊天记录到数据库
    param db：数据库会话
    param user_id: 用户ID
    param role:角色（user或assistant）
    param content:聊天内容
    return: 保存的记录对象
    """
    db_record=ChatRecord(user_id=user_id,role=role,content=content,create_time=datetime.now())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_chat_history(db, user_id: int, skip: int = 0, limit: int = 100):
    """
    获取用户聊天记录
    param db：数据库会话
    param user_id:用户ID
    param skip:跳过多少条记录
    param limit:最多返回多少条
    return: 聊天记录列表
    """
    return db.query(ChatRecord)\
        .filter(ChatRecord.user_id==user_id)\
        .order_by(ChatRecord.create_time.asc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def delete_chat_history(db, user_id: int):
    """
    删除指定用户聊天记录
    param db：数据库会话
    param user_id:用户ID
    return：删除的记录数
    """
    deleted_count = db.query(ChatRecord)\
        .filter(ChatRecord.user_id==user_id)\
        .delete()
    db.commit()
    return deleted_count

if __name__ == "__main__":
    db=next(get_db())
    text_user = create_user(db,"test_user","123456")
    print(f"创建用户：{text_user.username}，ID：{text_user.id}")
    print(f"验证密码（正确）：{verify_password('123456',text_user.password_hash)}")
