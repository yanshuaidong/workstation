const { getFuturesNews } = require('./src/utils/eastmoney_futures_scraper');

async function testFastScraper() {
    console.log('开始测试快速爬虫...');
    
    try {
        // 测试黄金期货新闻，使用15秒超时
        console.log('\n=== 测试黄金期货新闻（15秒超时）===');
        const startTime = Date.now();
        
        const goldNews = await getFuturesNews(
            'https://futures.eastmoney.com/a/ahj.html',
            '',
            15000 // 15秒超时
        );
        
        const endTime = Date.now();
        const duration = endTime - startTime;
        
        console.log(`黄金期货新闻数量: ${goldNews.length}`);
        console.log(`总耗时: ${duration}ms`);
        
        if (goldNews.length > 0) {
            console.log('前3条新闻:');
            goldNews.slice(0, 3).forEach((news, index) => {
                console.log(`${index + 1}. ${news.title} (${news.time})`);
            });
        }
        
        // 测试白银期货新闻，使用20秒超时
        console.log('\n=== 测试白银期货新闻（20秒超时）===');
        const startTime2 = Date.now();
        
        const silverNews = await getFuturesNews(
            'https://futures.eastmoney.com/a/aby.html',
            '',
            20000 // 20秒超时
        );
        
        const endTime2 = Date.now();
        const duration2 = endTime2 - startTime2;
        
        console.log(`白银期货新闻数量: ${silverNews.length}`);
        console.log(`总耗时: ${duration2}ms`);
        
        if (silverNews.length > 0) {
            console.log('前3条新闻:');
            silverNews.slice(0, 3).forEach((news, index) => {
                console.log(`${index + 1}. ${news.title} (${news.time})`);
            });
        }
        
        console.log('\n快速测试完成！');
        
    } catch (error) {
        console.error('测试过程中发生错误:', error);
    }
}

// 运行测试
testFastScraper(); 