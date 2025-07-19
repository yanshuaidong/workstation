const express = require('express');
const app = express();

// 设置端口
const port = 3000;

// 路由处理
app.get('/', (req, res) => {
  res.send('Hello World!');
});

// 启动服务器
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
