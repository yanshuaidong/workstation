const httpClient = require('../utils/httpClient');
const config = require('../config/config');

class OpenCtpService {
  constructor() {
    this.baseUrl = config.externalApi.openctp.baseUrl;
    this.endpoints = config.externalApi.openctp.endpoints;
    this.headers = config.externalApi.openctp.headers;
  }

  /**
   * 构建查询参数字符串
   */
  buildQueryParams(params) {
    const searchParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
        searchParams.append(key, params[key]);
      }
    });
    
    return searchParams.toString();
  }

  /**
   * 获取市场数据
   * @param {string} areas - 国家/地区，多个值用逗号分隔
   */
  async fetchMarkets(areas = '') {
    try {
      const params = { areas };
      const queryString = this.buildQueryParams(params);
      const url = `${this.baseUrl}${this.endpoints.markets}${queryString ? '?' + queryString : ''}`;

      const response = await httpClient.get(url, {
        headers: this.headers
      });

      return response;
    } catch (error) {
      throw new Error(`获取市场数据失败: ${error.message}`);
    }
  }

  /**
   * 获取品种数据
   * @param {string} types - 商品类型，多个值用逗号分隔
   * @param {string} areas - 国家/地区，多个值用逗号分隔
   * @param {string} markets - 交易所列表，多个值用逗号分隔
   * @param {string} products - 品种列表，多个值用逗号分隔
   */
  async fetchProducts(types = '', areas = '', markets = '', products = '') {
    try {
      const params = { types, areas, markets, products };
      const queryString = this.buildQueryParams(params);
      const url = `${this.baseUrl}${this.endpoints.products}${queryString ? '?' + queryString : ''}`;

      const response = await httpClient.get(url, {
        headers: this.headers
      });

      return response;
    } catch (error) {
      throw new Error(`获取品种数据失败: ${error.message}`);
    }
  }

  /**
   * 获取合约数据
   * @param {string} types - 商品类型，多个值用逗号分隔
   * @param {string} areas - 国家/地区，多个值用逗号分隔
   * @param {string} markets - 交易所列表，多个值用逗号分隔
   * @param {string} products - 品种列表，多个值用逗号分隔
   */
  async fetchInstruments(types = '', areas = '', markets = '', products = '') {
    try {
      const params = { types, areas, markets, products };
      const queryString = this.buildQueryParams(params);
      const url = `${this.baseUrl}${this.endpoints.instruments}${queryString ? '?' + queryString : ''}`;

      const response = await httpClient.get(url, {
        headers: this.headers
      });

      return response;
    } catch (error) {
      throw new Error(`获取合约数据失败: ${error.message}`);
    }
  }

  /**
   * 获取价格数据
   * @param {string} types - 商品类型，多个值用逗号分隔
   * @param {string} areas - 国家/地区，多个值用逗号分隔
   * @param {string} markets - 交易所列表，多个值用逗号分隔
   * @param {string} products - 品种列表，多个值用逗号分隔
   */
  async fetchPrices(types = '', areas = '', markets = '', products = '') {
    try {
      const params = { types, areas, markets, products };
      const queryString = this.buildQueryParams(params);
      const url = `${this.baseUrl}${this.endpoints.prices}${queryString ? '?' + queryString : ''}`;

      const response = await httpClient.get(url, {
        headers: this.headers
      });

      return response;
    } catch (error) {
      throw new Error(`获取价格数据失败: ${error.message}`);
    }
  }
}

module.exports = new OpenCtpService(); 