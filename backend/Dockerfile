FROM python:3.13-slim

# 时区与 locale
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 先装依赖（这一层缓存命中率高，代码改动不会重装）
COPY requirements.txt .
RUN pip install -r requirements.txt

# 再拷代码
COPY . .

# 非 root 运行（生产安全基线）
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 健康检查：访问根路径，FastAPI 会返回 200
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# 生产模式启动（不用 reload）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
