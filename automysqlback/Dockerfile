# 后端服务 Dockerfile（轻量级版本 - 已移除浏览器支持）
FROM python:3.10-slim

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 安装系统依赖（移除了浏览器相关依赖）
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    sed -i 's@deb.debian.org@mirrors.aliyun.com@g; s@security.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list \
 && printf 'Acquire::Retries "3"; Acquire::http::Timeout "15"; Acquire::https::Timeout "15";\n' > /etc/apt/apt.conf.d/99retries \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc g++ pkg-config default-libmysqlclient-dev curl wget ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# pip 默认源切清华（全局），并缓存 pip 目录（BuildKit）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 先拷 requirements（最大化利用层缓存）
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 拷贝业务代码
COPY . .

EXPOSE 7001

# 健康检查（用 curl）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:7001/api/settings || exit 1

CMD ["python", "start.py"]
