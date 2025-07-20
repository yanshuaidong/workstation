# 东方财富期货咨询抓取工具

这是一个专门用于抓取东方财富期货咨询的工具，基于 Puppeteer 实现。

## 核心方法

### `getFuturesNews(url, keyword, waitTime)`
获取期货相关新闻数据

**参数：**
- `url` (string): 目标网页URL，例如：`'https://futures.eastmoney.com/a/aps.html'`
- `keyword` (string, 可选): 过滤关键字，例如：`'多晶硅'`
- `waitTime` (number, 可选): 等待时间（毫秒），默认：`10000`

**返回：**
- `Array`: 新闻数据数组，每个元素包含：
  - `title`: 新闻标题
  - `time`: 发布时间
  - `link`: 新闻链接

**示例：**
```javascript
const { getFuturesNews } = require('./eastmoney_futures_scraper');

const goldNews = await getFuturesNews('https://futures.eastmoney.com/a/aps.html', '多晶硅');
```



## 安装依赖

```bash
npm install puppeteer
```

## 使用示例

```javascript
const { getFuturesNews } = require('./eastmoney_futures_scraper');

async function main() {
    try {
        const news = await getFuturesNews('https://futures.eastmoney.com/a/aps.html', '多晶硅');
        console.log('获取到的新闻:', news);
    } catch (error) {
        console.error('错误:', error);
    }
}

main();
``` 