from sqlalchemy import create_engine,Column,Integer,String,Text,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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

#聊天记录表模型
class ChatRecord(Base):
    __tablename__ = "chat_records"  #指定表名

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50),nullable=False)
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

def save_and_record(db,user_id:str,role:str,content:str):
    """
    保存单条聊天记录到数据库
    param db：数据库会话
    param role:角色（user或assistant）
    param content:聊天内容
    return: 保存的记录对象
    """
    db_record=ChatRecord(user_id=user_id,role=role,content=content,create_time=datetime.now())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_chat_history(db,user_id:str,skip:int=0,limit:int=100):
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

def delete_chat_history(db,user_id:str):
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
    count=delete_chat_history(db,"default_user")
    print(f"已删除{count}条记录")