const httpClient = require('../utils/httpClient');
const config = require('../config/config');

class VarietiesService {
  constructor() {
    this.baseUrl = config.externalApi.jiaoyikecha.baseUrl + '/ajax';
    this.headers = config.externalApi.jiaoyikecha.headers;
  }

  /**
   * 获取所有品种数据（调用真实API）
   */
  async fetchAllVarieties() {
    try {
      const url = `${this.baseUrl}/all_varieties.php?v=92c571cf`;
      
      const response = await httpClient.post(url, '', {
        headers: {
          ...this.headers,
          'content-length': '0'
        }
      });

      return response;
    } catch (error) {
      throw new Error(`获取所有品种数据失败: ${error.message}`);
    }
  }

  /**
   * 获取品种数据（原有方法，保持向后兼容）
   */
  async fetchVarieties() {
    try {
      // 调用新的真实API方法
      return await this.fetchAllVarieties();
    } catch (error) {
      // 如果API调用失败，返回示例数据作为备用
      console.warn('API调用失败，使用示例数据:', error.message);
      return {
        varieties: [
          { id: 1, name: '螺纹钢', code: 'rb', market: '上海期货交易所' },
          { id: 2, name: '多晶硅', code: 'ps', market: '广州期货交易所' }
        ],
        total: 2,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * 获取最近合约数据
   */
  async fetchRecentContracts(variety = '螺纹钢', date = '') {
    try {
      const url = `${this.baseUrl}/recent_contracts.php?v=92c571cf`;
      
      // URL编码品种名称
      const encodedVariety = encodeURIComponent(variety);
      const data = `variety=${encodedVariety}&date=${date}`;

      const response = await httpClient.post(url, data, {
        headers: {
          ...this.headers,
          'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      });

      return response;
    } catch (error) {
      throw new Error(`获取最近合约数据失败: ${error.message}`);
    }
  }

  /**
   * 获取品种结构数据
   */
  async fetchVarietyStructure(variety = '多晶硅', code = 'ps2509', brokerType = 'all') {
    try {
      const url = `${this.baseUrl}/variety_structure.php?v=92c571cf`;
      
      // URL编码品种名称
      const encodedVariety = encodeURIComponent(variety);
      const data = `variety=${encodedVariety}&code=${code}&broker_type=${brokerType}`;

      const response = await httpClient.post(url, data, {
        headers: {
          ...this.headers,
          'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      });

      return response;
    } catch (error) {
      throw new Error(`获取品种结构数据失败: ${error.message}`);
    }
  }

  /**
   * 获取品种日期数据
   */
  async fetchVarietyDates(variety = '螺纹钢') {
    try {
      const url = `${this.baseUrl}/variety_dates.php?v=92c571cf`;
      
      // URL编码品种名称
      const encodedVariety = encodeURIComponent(variety);
      const data = `variety=${encodedVariety}`;

      const response = await httpClient.post(url, data, {
        headers: {
          ...this.headers,
          'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      });

      return response;
    } catch (error) {
      throw new Error(`获取品种日期数据失败: ${error.message}`);
    }
  }

  /**
   * 获取品种盈亏数据
   */
  async fetchVarietyProfitLoss(variety = '螺纹钢', date1 = '2024-07-01', date2 = '') {
    try {
      const url = `${this.baseUrl}/variety_profit_loss.php?v=92c571cf`;
      
      // URL编码品种名称
      const encodedVariety = encodeURIComponent(variety);
      const data = `variety=${encodedVariety}&date1=${date1}&date2=${date2}`;

      const response = await httpClient.post(url, data, {
        headers: {
          ...this.headers,
          'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      });

      return response;
    } catch (error) {
      throw new Error(`获取品种盈亏数据失败: ${error.message}`);
    }
  }
}

module.exports = new VarietiesService(); 