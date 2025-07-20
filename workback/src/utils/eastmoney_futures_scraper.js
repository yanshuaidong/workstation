const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

/**
 * 设置Puppeteer浏览器，配置为无头模式
 * @returns {Promise<Browser|null>} 浏览器实例或null
 */
async function setupBrowser() {
    try {
        console.log('正在启动Puppeteer浏览器...');
        const browser = await puppeteer.launch({
            headless: "new",
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ],
            timeout: 30000
        });
        console.log('Puppeteer浏览器启动成功');
        return browser;
    } catch (error) {
        console.error('无法启动浏览器:', error.message);
        return null;
    }
}

/**
 * 使用Puppeteer请求网页并保存渲染后的数据
 * @param {string} url - 要请求的网页URL
 * @param {string} saveDir - 保存文件的目录
 * @param {number} waitTime - 等待页面加载的时间（毫秒）
 * @returns {Promise<boolean>} 是否成功
 */
async function fetchAndSaveWebpage(url, saveDir = 'public', waitTime = 10000) {
    let browser = null;
    let page = null;
    
    try {
        // 确保保存目录存在
        await fs.mkdir(saveDir, { recursive: true });
        
        // 启动浏览器
        browser = await setupBrowser();
        if (!browser) {
            return false;
        }
        
        // 创建新页面
        page = await browser.newPage();
        
        // 设置用户代理
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        // 设置视口大小
        await page.setViewport({ width: 1920, height: 1080 });
        
        // 访问页面
        await page.goto(url, { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        // 等待特定元素加载完成
        try {
            await page.waitForSelector('#newsListContent', { timeout: 10000 });
        } catch (error) {
            // 继续处理，即使元素未找到
        }
        
        // 滚动页面以触发懒加载
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        await page.evaluate(() => {
            window.scrollTo(0, 0);
        });
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 额外等待时间
        await new Promise(resolve => setTimeout(resolve, waitTime));
        
        // 获取页面内容
        const pageContent = await page.content();
        const pageTitle = await page.title();
        
        // 生成时间戳
        const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, '').replace('T', '_');
        
        // 保存HTML内容
        const htmlFilename = `eastmoney_futures_puppeteer_${timestamp}.html`;
        const htmlFilepath = path.join(saveDir, htmlFilename);
        
        await fs.writeFile(htmlFilepath, pageContent, 'utf-8');
        
        // 保存元数据
        const metadata = {
            url: url,
            timestamp: timestamp,
            page_title: pageTitle,
            content_length: pageContent.length,
            method: 'puppeteer_chrome',
            wait_time: waitTime,
            saved_files: {
                html: htmlFilename
            },
            fetch_time: new Date().toISOString()
        };
        
        const metadataFilename = `eastmoney_futures_puppeteer_metadata_${timestamp}.json`;
        const metadataFilepath = path.join(saveDir, metadataFilename);
        
        await fs.writeFile(metadataFilepath, JSON.stringify(metadata, null, 2), 'utf-8');
        
        return true;
        
    } catch (error) {
        console.error('发生错误:', error.message);
        return false;
    } finally {
        if (page) {
            await page.close();
        }
        if (browser) {
            await browser.close();
        }
    }
}

/**
 * 从HTML内容中提取新闻数据
 * @param {string} htmlContent - HTML内容
 * @returns {Array} 新闻数据数组
 */
function extractNewsData(htmlContent) {
    const newsList = [];
    
    try {
        console.log('开始解析HTML内容，内容长度:', htmlContent.length);
        
        // 使用正则表达式提取新闻列表项
        const newsItemRegex = /<li[^>]*class="[^"]*list-two[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*target="_blank">.*?<span[^>]*class="[^"]*list-content[^"]*"[^>]*>([^<]*)<\/span>.*?<span[^>]*class="[^"]*list-time[^"]*"[^>]*>([^<]*)<\/span>.*?<\/a>.*?<\/li>/gs;
        
        let match;
        let matchCount = 0;
        while ((match = newsItemRegex.exec(htmlContent)) !== null) {
            const [, link, title, time] = match;
            newsList.push({
                title: title.trim(),
                time: time.trim(),
                link: link.trim()
            });
            matchCount++;
        }
        
        console.log(`正则表达式匹配到 ${matchCount} 条新闻`);
        
        // 如果正则表达式没有匹配到数据，尝试其他选择器
        if (matchCount === 0) {
            console.log('正则表达式未匹配到数据，尝试备用解析方法...');
            return extractNewsDataAlternative(htmlContent);
        }
        
        return newsList;
    } catch (error) {
        console.error('解析HTML数据时出错:', error.message);
        return [];
    }
}

/**
 * 备用新闻数据提取方法
 * @param {string} htmlContent - HTML内容
 * @returns {Array} 新闻数据数组
 */
function extractNewsDataAlternative(htmlContent) {
    const newsList = [];
    
    try {
        console.log('使用备用方法解析新闻数据...');
        
        // 尝试多种正则表达式模式
        const patterns = [
            // 模式1：更宽松的匹配
            /<a[^>]*href="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)<\/span>.*?<span[^>]*>([^<]*)<\/span>.*?<\/a>/gs,
            // 模式2：查找包含新闻链接的元素
            /<a[^>]*href="([^"]*)"[^>]*target="_blank"[^>]*>.*?([^<]+)<\/a>/gs,
            // 模式3：查找时间戳
            /<span[^>]*class="[^"]*time[^"]*"[^>]*>([^<]*)<\/span>/gs
        ];
        
        for (let i = 0; i < patterns.length; i++) {
            const pattern = patterns[i];
            const matches = htmlContent.match(pattern);
            if (matches && matches.length > 0) {
                console.log(`备用模式 ${i + 1} 找到 ${matches.length} 个匹配`);
                // 这里可以根据具体模式处理数据
                break;
            }
        }
        
        // 如果还是没找到，尝试查找页面中的任何链接和文本
        const linkMatches = htmlContent.match(/<a[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/gs);
        if (linkMatches) {
            console.log(`找到 ${linkMatches.length} 个链接元素`);
            // 过滤出可能是新闻的链接
            const newsLinks = linkMatches.filter(link => 
                link.includes('news') || link.includes('article') || link.includes('html')
            );
            console.log(`过滤后找到 ${newsLinks.length} 个可能的新闻链接`);
        }
        
        return newsList;
    } catch (error) {
        console.error('备用解析方法出错:', error.message);
        return [];
    }
}

/**
 * 根据关键字过滤新闻数据
 * @param {Array} newsList - 新闻数据数组
 * @param {string} keyword - 过滤关键字
 * @returns {Array} 过滤后的新闻数据数组
 */
function filterNewsByKeyword(newsList, keyword) {
    if (!keyword || keyword.trim() === '') {
        return newsList;
    }
    
    const filteredList = newsList.filter(news => 
        news.title.includes(keyword.trim())
    );
    
    return filteredList;
}

/**
 * 获取期货相关新闻数据
 * @param {string} url - 目标网页URL
 * @param {string} keyword - 过滤关键字（可选）
 * @param {number} waitTime - 前端超时时间（毫秒）
 * @returns {Promise<Array>} 新闻数据数组
 */
async function getFuturesNews(url, keyword = '', waitTime = 10000) {
    let browser = null;
    let page = null;
    const startTime = Date.now(); // 记录开始时间
    
    try {
        console.log(`开始获取期货新闻，URL: ${url}, 前端超时时间: ${waitTime}ms`);
        
        // 启动浏览器
        browser = await setupBrowser();
        if (!browser) {
            console.error('浏览器启动失败');
            return [];
        }
        
        // 创建新页面
        page = await browser.newPage();
        console.log('页面创建成功');
        
        // 设置用户代理
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        // 设置视口大小
        await page.setViewport({ width: 1920, height: 1080 });
        
        // 设置请求拦截，跳过图片等资源以加快加载速度
        await page.setRequestInterception(true);
        page.on('request', (req) => {
            if (['image', 'stylesheet', 'font'].includes(req.resourceType())) {
                req.abort();
            } else {
                req.continue();
            }
        });
        
        console.log('正在访问页面...');
        // 访问页面，使用更快的加载策略
        const response = await page.goto(url, { 
            waitUntil: 'domcontentloaded', // 改为domcontentloaded，更快
            timeout: Math.min(waitTime - 5000, 30000) // 预留5秒给其他操作
        });
        
        console.log(`页面访问完成，状态码: ${response.status()}`);
        
        // 快速检查页面是否加载完成
        try {
            await page.waitForSelector('body', { timeout: 5000 });
            console.log('页面基本元素加载完成');
        } catch (error) {
            console.log('等待页面元素超时，继续处理');
        }
        
        // 等待新闻列表容器，但时间要短
        let newsContainerFound = false;
        try {
            await page.waitForSelector('#newsListContent', { timeout: 8000 });
            console.log('新闻列表容器加载完成');
            newsContainerFound = true;
        } catch (error) {
            console.log('新闻列表容器未找到，尝试其他选择器');
            try {
                await page.waitForSelector('.news-list', { timeout: 5000 });
                console.log('备用新闻列表容器加载完成');
                newsContainerFound = true;
            } catch (error2) {
                console.log('备用新闻列表容器也未找到，继续处理');
            }
        }
        
        // 如果找到了新闻容器，进行快速滚动
        if (newsContainerFound) {
            console.log('开始快速滚动页面...');
            // 快速滚动，减少等待时间
            await page.evaluate(() => {
                window.scrollTo(0, document.body.scrollHeight);
            });
            await new Promise(resolve => setTimeout(resolve, 3000)); // 等待3秒
            
            await page.evaluate(() => {
                window.scrollTo(0, 0);
            });
            await new Promise(resolve => setTimeout(resolve, 3000)); // 等待3秒
        }
        
        // 计算剩余时间，动态调整等待
        const elapsedTime = Date.now() - startTime; // 正确计算已用时间
        const remainingTime = Math.max(2000, waitTime - elapsedTime - 5000); // 至少保留2秒，预留5秒给处理
        
        console.log(`已用时间: ${elapsedTime}ms, 动态等待时间: ${remainingTime}ms`);
        await new Promise(resolve => setTimeout(resolve, remainingTime));
        
        // 获取页面内容
        console.log('获取页面内容...');
        const pageContent = await page.content();
        console.log(`页面内容获取完成，长度: ${pageContent.length}`);
        
        // 保存页面内容用于调试
        const debugDir = path.join(process.cwd(), 'debug');
        await fs.mkdir(debugDir, { recursive: true });
        const debugFile = path.join(debugDir, `debug_${Date.now()}.html`);
        await fs.writeFile(debugFile, pageContent, 'utf-8');
        console.log(`调试文件已保存: ${debugFile}`);
        
        // 提取新闻数据
        const allNews = extractNewsData(pageContent);
        console.log(`提取到 ${allNews.length} 条新闻`);
        
        // 根据关键字过滤
        const filteredNews = filterNewsByKeyword(allNews, keyword);
        console.log(`过滤后剩余 ${filteredNews.length} 条新闻`);
        
        return filteredNews;
        
    } catch (error) {
        console.error('获取期货新闻时发生错误:', error.message);
        console.error('错误堆栈:', error.stack);
        return [];
    } finally {
        if (page) {
            try {
                await page.close();
                console.log('页面已关闭');
            } catch (error) {
                console.error('关闭页面时出错:', error.message);
            }
        }
        if (browser) {
            try {
                await browser.close();
                console.log('浏览器已关闭');
            } catch (error) {
                console.error('关闭浏览器时出错:', error.message);
            }
        }
    }
}

/**
 * 从本地HTML文件提取新闻数据
 * @param {string} htmlFilePath - HTML文件路径
 * @param {string} keyword - 过滤关键字（可选）
 * @returns {Promise<Array>} 新闻数据数组
 */
async function getFuturesNewsFromFile(htmlFilePath, keyword = '') {
    try {
        // 读取HTML文件
        const htmlContent = await fs.readFile(htmlFilePath, 'utf-8');
        
        // 提取新闻数据
        const allNews = extractNewsData(htmlContent);
        
        // 根据关键字过滤
        const filteredNews = filterNewsByKeyword(allNews, keyword);
        
        return filteredNews;
        
    } catch (error) {
        console.error('从文件提取期货新闻时发生错误:', error.message);
        return [];
    }
}

module.exports = {
    fetchAndSaveWebpage,
    setupBrowser,
    getFuturesNews,
    getFuturesNewsFromFile,
    extractNewsData,
    filterNewsByKeyword
}; 