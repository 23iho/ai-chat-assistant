import os
from dotenv import load_dotenv
from datetime import datetime , timedelta , timezone
from jose import JWTError , jwt
from fastapi import Depends , HTTPException , status
from fastapi.security import OAuth2PasswordBearer
from database import get_db , get_user_by_username
from sqlalchemy.orm import Session

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int (os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES",1440))

def create_access_token(data:dict , expires_delta:timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode , SECRET_KEY , algorithm=ALGORITHM)
    return encoded_jwt,expire
def verify_access_token(token:str):
    try:
        payload = jwt.decode(token,SECRET_KEY , algorithms=[ALGORITHM]) 
        user_id:int = payload.get("user_id")
        username:str = payload.get("username")

        if user_id is None or username is None:
            return None
        return {"user_id":user_id,"username":username}
    except JWTError:
        return None   
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/oauth")
def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供token，请先登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token_data = verify_access_token(token)
    if not token_data: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效token，请重新登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = get_user_by_username(db, username=token_data["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


      