# workfront

`workfront` 是个人期货数据系统的前端项目，负责提供期货行情展示、消息面分析、消息跟踪、持仓管理和量化策略可视化界面。

## 技术栈

- Vue 3
- Vue Router 4
- Element Plus
- ECharts
- Axios
- Vue CLI 5

## 功能模块

当前前端包含以下业务模块：

- 消息面分析
- 消息跟踪
- 我的持仓
- 期货 K 线图
- 量化策略：信号面板、操作建议、持仓盈亏、资金曲线、K 线展示、池子管理

主要路由如下：

- `/news-analysis`
- `/news-tracking`
- `/positions`
- `/futures-chart`
- `/trading/signals`
- `/trading/operations`
- `/trading/positions`
- `/trading/curve`
- `/trading/kline`
- `/trading/pool`

## 项目结构

```text
workfront/
├─ public/                 静态资源
├─ src/
│  ├─ assets/              全局样式与资源文件
│  ├─ components/          通用业务组件
│  ├─ router/              路由配置
│  ├─ utils/               请求封装、设备适配、图表配置
│  ├─ views/
│  │  ├─ futures-chart/    K 线与事件管理页面
│  │  └─ trading/          量化策略页面
│  ├─ api.js               前端接口地址定义
│  ├─ App.vue              应用入口组件
│  └─ main.js              应用初始化
├─ tests/                  图表配置相关测试文件
├─ vue.config.js           Vue CLI 与开发代理配置
├─ nginx.conf              生产环境 Nginx 配置
├─ Dockerfile              前端镜像构建文件
└─ package.json            依赖与脚本配置
```

## 开发环境

建议使用：

- Node.js 18

安装依赖：

```bash
npm install
```

启动本地开发服务器：

```bash
npm run dev
```

默认开发地址：

```text
http://localhost:8080
```

代码检查：

```bash
npm run lint
```

构建生产包：

```bash
npm run build
```

构建产物输出到：

```text
dist/
```

## 接口联调

前端通过相对路径 `/api-a` 调用后端接口。

本地开发时，`vue.config.js` 中的代理会将请求转发到：

```text
http://localhost:7001/api
```

转发规则如下：

- 前端请求路径：`/api-a/...`
- 后端实际路径：`/api/...`

接口定义集中在 [src/api.js](/D:/ysd/workstation/workfront/src/api.js)，请求封装位于 [src/utils/request.js](/D:/ysd/workstation/workfront/src/utils/request.js)。

## 运行说明

如果需要本地联调，请先启动后端服务：

```bash
cd ../automysqlback
python start.py
```

后端默认监听 `7001` 端口。

## 页面与交互特性

- Element Plus 使用中文语言包
- 全量注册 Element Plus 图标
- 启动时自动执行移动端视口适配
- 开发环境显示错误覆盖层，并过滤 `ResizeObserver` 的无效运行时提示
- 生产构建会进行代码分包，并关闭 source map

## Docker 构建

项目提供多阶段 Docker 构建：

1. 使用 `node:18-alpine` 安装依赖并执行前端构建
2. 使用 `nginx:alpine` 承载 `dist/` 静态资源

在仓库根目录可通过部署脚本统一启动相关服务：

```bash
./deploy.sh deploy
./deploy.sh start
./deploy.sh stop
./deploy.sh restart
```

## 相关文件

- [package.json](/D:/ysd/workstation/workfront/package.json)
- [vue.config.js](/D:/ysd/workstation/workfront/vue.config.js)
- [src/router/index.js](/D:/ysd/workstation/workfront/src/router/index.js)
- [src/main.js](/D:/ysd/workstation/workfront/src/main.js)
