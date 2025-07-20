const newsService = require('../services/newsService');
const { responseHandler } = require('../utils/responseHandler');

class NewsController {
  /**
   * 获取可用的新闻提供商列表
   */
  async getNewsProviders(req, res) {
    try {
      const providers = await newsService.getAvailableProviders();
      responseHandler.success(res, providers, '新闻提供商列表获取成功');
    } catch (error) {
      console.error('获取新闻提供商列表失败:', error);
      responseHandler.error(res, '新闻提供商列表获取失败', 500);
    }
  }

  /**
   * 获取期货新闻
   */
  async getFuturesNews(req, res) {
    try {
      const { provider, variety, keyword, waitTime } = req.body;
      
      if (!provider || !variety) {
        return responseHandler.error(res, '缺少必要参数：provider 和 variety', 400);
      }

      const news = await newsService.fetchFuturesNews(provider, variety, keyword, waitTime);
      responseHandler.success(res, news, '期货新闻获取成功');
    } catch (error) {
      console.error('获取期货新闻失败:', error);
      responseHandler.error(res, '期货新闻获取失败', 500);
    }
  }

  /**
   * 获取指定提供商的可用品种列表
   */
  async getVarietiesByProvider(req, res) {
    try {
      const { provider } = req.body;
      
      if (!provider) {
        return responseHandler.error(res, '缺少必要参数：provider', 400);
      }

      const varieties = await newsService.getVarietiesByProvider(provider);
      responseHandler.success(res, varieties, '品种列表获取成功');
    } catch (error) {
      console.error('获取品种列表失败:', error);
      responseHandler.error(res, '品种列表获取失败', 500);
    }
  }
}

module.exports = new NewsController(); 