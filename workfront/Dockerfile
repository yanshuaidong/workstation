# 前端构建 Dockerfile（极速国内源 + BuildKit 缓存）
# ===== 构建阶段 =====
FROM node:18-alpine AS build

# Alpine 源换阿里云（如需 apk 装包会更快；不装也无妨）
RUN sed -i 's@dl-cdn.alpinelinux.org@mirrors.aliyun.com@g' /etc/apk/repositories

WORKDIR /app

# 先拷依赖清单，最大化镜像层缓存
COPY package*.json ./

# 使用 npmmirror，并利用 BuildKit 的 npm 缓存（需 DOCKER_BUILDKIT=1）
RUN --mount=type=cache,target=/root/.npm \
    npm config set registry https://registry.npmmirror.com \
 && npm ci --prefer-offline --no-audit --fund=false

# 拷贝源码并构建
COPY . .
RUN npm run build

# ===== 运行阶段 =====
FROM nginx:alpine

# 可选：Alpine 源换阿里云，便于后续扩展（apk add）
RUN sed -i 's@dl-cdn.alpinelinux.org@mirrors.aliyun.com@g' /etc/apk/repositories

# 放置构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 自定义 nginx 配置（你已有）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
