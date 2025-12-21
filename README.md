# 个人期货系统

基于python的期货系统

定时表：
database
在交易日（周一至周五）的下午5点自动更新期货股票国泰数据

quantlab
-quantlab\futures 在交易日（周一至周五）的下午5点10分
-quantlab\institution 在交易日（周一至周五）的下午5点12分

spiderx

spiderx\clsnewscraper 运行40天，每1小时执行一次完整流程（爬取+AI分析）
spiderx\eastfutuscraper 运行40天，仅在交易日（周一到周五）的下午4点执行
spiderx\futurestop10 运行40天，仅在交易日（周一到周五）的下午5:30执行（期货收盘后）
spiderx\gthtposiscraper 运行40天，仅在交易日的下午6:30执行（期货收盘后）

spiderx\bbgnews 定时处理新闻（每天5:30/11:30/17:30/23:30）
spiderx\rtrsnews 定时处理新闻（每天5/11/17/23点，与彭博社错开1小时）

spiderx\chatgpthelper 每天执行6次：**2点、6点、10点、14点、18点、22点**（与Gemini错开2小时）
spiderx\geminihelper 每天执行6次：**4点、8点、12点、16点、20点、24点**





