# 后端服务 Dockerfile（极速国内源 + BuildKit 缓存）
FROM python:3.10-slim

# 环境
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 1) 换阿里云 Debian 源 + apt 重试 + 装 curl（供健康检查）+ Chrome浏览器
# 2) 使用 BuildKit 的 apt 缓存（需 DOCKER_BUILDKIT=1）
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    sed -i 's@deb.debian.org@mirrors.aliyun.com@g; s@security.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list \
 && printf 'Acquire::Retries "3"; Acquire::http::Timeout "15"; Acquire::https::Timeout "15";\n' > /etc/apt/apt.conf.d/99retries \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc g++ pkg-config default-libmysqlclient-dev curl \
      wget gnupg2 software-properties-common \
 && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      google-chrome-stable \
      xvfb \
 && rm -rf /var/lib/apt/lists/*

# 3) pip 默认源切清华（全局），并缓存 pip 目录（BuildKit）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 4) 先拷 requirements（最大化利用层缓存）
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 5) 拷贝业务代码
COPY . .

EXPOSE 7001

# 健康检查（用 curl）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:7001/api/settings || exit 1

CMD ["python", "start.py"]
