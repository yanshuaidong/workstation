# 老接口 & 老前端清理计划

> **执行前提**：新 trading 系统已全部验证通过（三个面板数据正常、资金曲线正常、daily_run.py 至少跑过一次完整流程）。
> 本计划的所有操作均为不可逆删除，验证完成前不执行。

---

## 一、涉及文件清单

### 后端

| 文件 / 代码位置 | 操作 |
|----------------|------|
| `automysqlback/routes/assistant_routes.py` | 整文件删除 |
| `automysqlback/app.py` 第28行 `from routes import ... assistant_bp` | 删除 `assistant_bp` 的导入 |
| `automysqlback/app.py` 第132行 `app.register_blueprint(assistant_bp, ...)` | 删除该行 |

### 前端（视图文件）

| 文件 | 操作 |
|------|------|
| `workfront/src/views/assistant/index.vue` | 删除 |
| `workfront/src/views/assistant/SignalsView.vue` | 删除 |
| `workfront/src/views/assistant/OperationsView.vue` | 删除 |
| `workfront/src/views/assistant/PositionsView.vue` | 删除 |
| `workfront/src/views/assistant/CurveView.vue` | 删除 |
| `workfront/src/views/assistant/KlineView.vue` | 删除 |
| `workfront/src/views/assistant/AssistantContextChart.vue` | 删除 |
| `workfront/src/views/assistant/signalTableSchema.js` | 删除 |
| `workfront/src/views/assistant/`（目录） | 目录清空后删除 |

### 前端（路由 & 导航）

| 文件 | 需修改的内容 |
|------|-------------|
| `workfront/src/router/index.js` 第7–12行 | 删除6行 Assistant* 的 import |
| `workfront/src/router/index.js` 第53–58行附近 | 删除 `/assistant` 路由及其子路由配置块 |
| `workfront/src/App.vue` 第46行 | 删除移动端菜单 `el-menu-item index="/assistant/signals"` |
| `workfront/src/App.vue` 第85行 | 删除桌面端菜单 `el-menu-item index="/assistant/signals"` |
| `workfront/src/App.vue` 第136行 | 删除 `startsWith('/assistant')` 的分支逻辑 |

---

## 二、执行顺序

```
Step 1  后端清理
        1. 删除 assistant_routes.py
        2. 修改 app.py：删除 assistant_bp 导入行 + register_blueprint 行
        3. 重启后端，确认无报错，访问 /api/trading/signals 正常

Step 2  前端清理
        1. 删除 workfront/src/views/assistant/ 整目录
        2. 修改 router/index.js：删除6个 import + /assistant 路由块
        3. 修改 App.vue：删除两处菜单项 + 第136行分支逻辑
        4. npm run build 确认编译通过，无 lint 报错

Step 3  验证
        1. 访问前端，导航栏中 /assistant 入口已消失
        2. 直接访问 /assistant 返回404或重定向到首页（取决于路由兜底配置）
        3. 后端 /api/assistant/* 接口返回404
        4. 新 /trading 三个面板功能不受影响
```

---

## 三、不在本次清理范围内

- `test/assistant/` 目录（实验性代码，保留作参考，不影响生产）
- `test/plan2/` 目录（同上）
- 数据库中的 `assistant_*` 四张表已在 `create_tables.py` 的 Step 1 中删除，此处无需重复操作
