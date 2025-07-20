const { getFuturesNews } = require('./src/utils/eastmoney_futures_scraper');

async function testNewsScraper() {
    console.log('开始测试新闻爬虫...');
    
    try {
        // 测试黄金期货新闻
        console.log('\n=== 测试黄金期货新闻 ===');
        const goldNews = await getFuturesNews(
            'https://futures.eastmoney.com/a/ahj.html',
            '',
            30000 // 30秒等待时间
        );
        
        console.log(`黄金期货新闻数量: ${goldNews.length}`);
        if (goldNews.length > 0) {
            console.log('前3条新闻:');
            goldNews.slice(0, 3).forEach((news, index) => {
                console.log(`${index + 1}. ${news.title} (${news.time})`);
            });
        }
        
        // 测试白银期货新闻
        console.log('\n=== 测试白银期货新闻 ===');
        const silverNews = await getFuturesNews(
            'https://futures.eastmoney.com/a/aby.html',
            '',
            30000
        );
        
        console.log(`白银期货新闻数量: ${silverNews.length}`);
        if (silverNews.length > 0) {
            console.log('前3条新闻:');
            silverNews.slice(0, 3).forEach((news, index) => {
                console.log(`${index + 1}. ${news.title} (${news.time})`);
            });
        }
        
        console.log('\n测试完成！');
        
    } catch (error) {
        console.error('测试过程中发生错误:', error);
    }
}

// 运行测试
testNewsScraper(); 