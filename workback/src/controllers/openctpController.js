const openctpService = require('../services/openctpService');
const { responseHandler } = require('../utils/responseHandler');

class OpenCtpController {
  /**
   * 获取市场数据
   */
  async getMarkets(req, res) {
    try {
      const { areas } = req.body;
      const data = await openctpService.fetchMarkets(areas);
      responseHandler.success(res, data, '市场数据获取成功');
    } catch (error) {
      console.error('获取市场数据失败:', error);
      responseHandler.error(res, '市场数据获取失败', 500);
    }
  }

  /**
   * 获取品种数据
   */
  async getProducts(req, res) {
    try {
      const { types, areas, markets, products } = req.body;
      const data = await openctpService.fetchProducts(types, areas, markets, products);
      responseHandler.success(res, data, '品种数据获取成功');
    } catch (error) {
      console.error('获取品种数据失败:', error);
      responseHandler.error(res, '品种数据获取失败', 500);
    }
  }

  /**
   * 获取合约数据
   */
  async getInstruments(req, res) {
    try {
      const { types, areas, markets, products } = req.body;
      const data = await openctpService.fetchInstruments(types, areas, markets, products);
      responseHandler.success(res, data, '合约数据获取成功');
    } catch (error) {
      console.error('获取合约数据失败:', error);
      responseHandler.error(res, '合约数据获取失败', 500);
    }
  }

  /**
   * 获取价格数据
   */
  async getPrices(req, res) {
    try {
      const { types, areas, markets, products } = req.body;
      const data = await openctpService.fetchPrices(types, areas, markets, products);
      responseHandler.success(res, data, '价格数据获取成功');
    } catch (error) {
      console.error('获取价格数据失败:', error);
      responseHandler.error(res, '价格数据获取失败', 500);
    }
  }
}

module.exports = new OpenCtpController(); 