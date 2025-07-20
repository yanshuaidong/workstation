const { getFuturesNews } = require('../utils/eastmoney_futures_scraper');
const eastmoneyNewsConfig = require('../config/eastmoneyNews');
const newsProviders = require('../config/newsProviders');

class NewsService {
  /**
   * 获取可用的新闻提供商列表
   */
  async getAvailableProviders() {
    return newsProviders;
  }

  /**
   * 根据提供商获取可用品种列表
   * @param {string} provider 新闻提供商
   * @returns {Array} 品种列表
   */
  async getVarietiesByProvider(provider) {
    switch (provider) {
      case 'eastmoney':
        return Object.keys(eastmoneyNewsConfig).map(variety => ({
          name: variety,
          url: eastmoneyNewsConfig[variety]
        }));
      default:
        throw new Error(`不支持的新闻提供商: ${provider}`);
    }
  }

  /**
   * 获取期货新闻
   * @param {string} provider 新闻提供商
   * @param {string} variety 期货品种
   * @param {string} keyword 关键词过滤（可选）
   * @param {number} waitTime 前端超时时间（毫秒）
   * @returns {Array} 新闻数据
   */
  async fetchFuturesNews(provider, variety, keyword = '', waitTime = 60000) {
    try {
      console.log(`开始获取期货新闻 - 提供商: ${provider}, 品种: ${variety}, 关键词: ${keyword}, 前端超时时间: ${waitTime}ms`);
      
      switch (provider) {
        case 'eastmoney':
          return await this.fetchEastmoneyNews(variety, keyword, waitTime);
        default:
          throw new Error(`不支持的新闻提供商: ${provider}`);
      }
    } catch (error) {
      console.error('获取新闻失败:', error);
      throw error;
    }
  }

  /**
   * 获取东方财富期货新闻
   * @param {string} variety 期货品种
   * @param {string} keyword 关键词过滤
   * @param {number} waitTime 前端超时时间
   * @returns {Array} 新闻数据
   */
  async fetchEastmoneyNews(variety, keyword, waitTime) {
    const url = eastmoneyNewsConfig[variety];
    if (!url) {
      throw new Error(`不支持的期货品种: ${variety}`);
    }

    console.log(`开始抓取${variety}期货新闻，URL: ${url}`);
    
    // 创建超时Promise，使用前端传入的超时时间
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`前端超时，等待时间: ${waitTime}ms`));
      }, waitTime);
    });
    
    // 创建爬虫Promise，传入前端超时时间
    const scraperPromise = getFuturesNews(url, keyword, waitTime);
    
    try {
      // 使用Promise.race来处理超时
      const news = await Promise.race([scraperPromise, timeoutPromise]);
      
      // 数据格式化和验证
      const formattedNews = news.map(item => ({
        title: item.title || '',
        time: item.time || '',
        link: item.link || ''
      })).filter(item => item.title && item.time);

      console.log(`成功获取${formattedNews.length}条新闻`);
      return formattedNews;
      
    } catch (error) {
      console.error(`抓取${variety}期货新闻失败:`, error.message);
      
      // 如果是超时错误，返回空数组而不是抛出异常
      if (error.message.includes('超时')) {
        console.log('由于前端超时，返回空结果');
        return [];
      }
      
      throw error;
    }
  }
}

module.exports = new NewsService(); 