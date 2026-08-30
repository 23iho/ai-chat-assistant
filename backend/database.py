from sqlalchemy import create_engine,Column,Integer,String,Text,DateTime,ForeignKey,Index,inspect,text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import bcrypt
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
# echo 默认 False（生产环境不打印 SQL），需要排查问题时设 DB_ECHO=1
engine = create_engine(
    sql_url,
    echo=os.getenv("DB_ECHO", "0") == "1",
    pool_pre_ping=True,   # 连接池预检，避免拿到 MySQL wait_timeout 切断的连接
    pool_recycle=3600,    # 一小时回收连接
)
#创建基类
Base = declarative_base()
#创建会话工厂
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

#创建密码加密上下文
# 注：原本用 passlib，但它跟新版本 bcrypt (≥3.2) 不兼容，
# 直接用 bcrypt 包更稳。bcrypt 单向 72 字节限制由我们手动处理。
_BCRYPT_MAX_LEN = 72
class User(Base):
    __tablename__ = "users"  #指定表名

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50),unique=True,nullable=False,index=True)
    password_hash = Column(String(255),nullable=False)
    email = Column(String(100),unique=True,nullable=True)
    create_time = Column(DateTime,default=datetime.now)

#密码加密与验证
def get_password_hash(password: str) -> str:
    # bcrypt 单向 72 字节截断；超长密码直接拒绝，
    # Pydantic 那层 max_length=100 不会让这里被滥用
    pwd_bytes = password.encode("utf-8")[:_BCRYPT_MAX_LEN]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_LEN]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        # hash 字符串非法
        return False
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
class Conversation(Base):
    """会话（Conversation）：把同一话题的多条消息聚合在一起。

    删除会话时通过 relationship 的 cascade='all, delete-orphan'
    自动级联删除该会话下的所有 ChatRecord。
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), nullable=False, default="新对话")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    records = relationship(
        "ChatRecord",
        backref="conversation",
        cascade="all, delete-orphan",
    )


class ChatRecord(Base):
    __tablename__ = "chat_records"  #指定表名

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,  # 兼容老数据：建表前已有的记录没有 conversation_id
        index=True,
    )
    role = Column(String(20),nullable=False)  # "user" 或 "assistant"
    content = Column(Text,nullable=False)
    create_time = Column(DateTime,default=datetime.now,index=True)

#自动创建表（只对不存在的表生效，老表不会被改）
Base.metadata.create_all(bind=engine)


def ensure_schema():
    """轻量级 schema 演进：启动时给老库补齐缺失的列/索引。

    没用 Alembic 是因为项目还在早期迭代，全量 DDL 工具太重。
    这里只补"加列/加索引"这种非破坏性变更；
    破坏性的（比如改类型、删列）留给 Alembic。
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:
        if "chat_records" in existing_tables:
            cols = {c["name"] for c in inspector.get_columns("chat_records")}
            if "conversation_id" not in cols:
                conn.execute(text(
                    "ALTER TABLE chat_records ADD COLUMN conversation_id INT NULL"
                ))
            indexes = {ix["name"] for ix in inspector.get_indexes("chat_records")}
            # 复合索引 (user_id, conversation_id) 支持单会话内历史查询
            if "idx_chat_user_conv" not in indexes:
                conn.execute(text(
                    "CREATE INDEX idx_chat_user_conv "
                    "ON chat_records (user_id, conversation_id)"
                ))


ensure_schema()

#获取数据库连接
def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_and_record(db, user_id: int, role: str, content: str, conversation_id: int | None = None):
    """
    保存单条聊天记录到数据库

    param db：数据库会话
    param user_id:用户ID
    param role:角色（user或assistant）
    param content:聊天内容
    param conversation_id:所属会话ID（可空，兼容老数据）
    return: 保存的记录对象
    """
    db_record = ChatRecord(
        user_id=user_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        create_time=datetime.now(),
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


# ===== 会话（Conversation）相关 =====

def list_conversations(db, user_id: int, limit: int = 100):
    """列出某用户的所有会话，按最近更新时间倒序。"""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_conversation(db, conversation_id: int, user_id: int) -> Conversation | None:
    """获取一个会话（同时校验所有权，避免越权访问）。"""
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )


def create_conversation(db, user_id: int, title: str = "新对话") -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def rename_conversation(db, conversation_id: int, user_id: int, title: str) -> Conversation | None:
    conv = get_conversation(db, conversation_id, user_id)
    if conv:
        conv.title = title[:200]
        db.commit()
        db.refresh(conv)
    return conv


def touch_conversation(db, conversation_id: int):
    """会话被使用时刷新 updated_at，让它在列表里排到最前。"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.updated_at = datetime.now()
        db.commit()


def delete_conversation(db, conversation_id: int, user_id: int) -> int:
    """删除一个会话及其所有消息，返回消息删除条数。"""
    conv = get_conversation(db, conversation_id, user_id)
    if not conv:
        return 0
    deleted_records = (
        db.query(ChatRecord)
        .filter(ChatRecord.conversation_id == conversation_id)
        .delete()
    )
    db.delete(conv)
    db.commit()
    return deleted_records

def get_chat_history(db, user_id: int, skip: int = 0, limit: int = 100, conversation_id: int | None = None):
    """
    获取用户聊天记录（按时间升序，适合 /history 分页展示）。

    如果指定 conversation_id，则只返回该会话下的消息。
    """
    q = db.query(ChatRecord).filter(ChatRecord.user_id == user_id)
    if conversation_id is not None:
        q = q.filter(ChatRecord.conversation_id == conversation_id)
    return q.order_by(ChatRecord.create_time.asc()).offset(skip).limit(limit).all()

def get_latest_n_chat_history(db, user_id: int, n: int, conversation_id: int | None = None):
    """
    获取用户最近的 n 条聊天记录，按时间升序返回，用于上下文重建。

    实现上用 ORDER BY DESC + LIMIT n 一次取最新 n 条，再反转成正向时间序。
    这样 SQL 走索引一次就够，不必全表计数再 LIMIT 的笨办法。
    """
    q = db.query(ChatRecord).filter(ChatRecord.user_id == user_id)
    if conversation_id is not None:
        q = q.filter(ChatRecord.conversation_id == conversation_id)
    desc_records = q.order_by(ChatRecord.create_time.desc()).limit(n).all()
    return list(reversed(desc_records))

def delete_chat_history(db, user_id: int, conversation_id: int | None = None):
    """
    删除指定用户聊天记录。
    如果传 conversation_id，只删该会话下的；否则删全部（兼容老接口）。
    """
    q = db.query(ChatRecord).filter(ChatRecord.user_id == user_id)
    if conversation_id is not None:
        q = q.filter(ChatRecord.conversation_id == conversation_id)
    deleted_count = q.delete()
    db.commit()
    return deleted_count

if __name__ == "__main__":
    db=next(get_db())
    text_user = create_user(db,"test_user","123456")
    print(f"创建用户：{text_user.username}，ID：{text_user.id}")
    print(f"验证密码（正确）：{verify_password('123456',text_user.password_hash)}")
