const varietiesService = require('../services/varietiesService');
const { responseHandler } = require('../utils/responseHandler');

class VarietiesController {
  /**
   * 获取所有品种数据
   */
  async getAllVarieties(req, res) {
    try {
      const data = await varietiesService.fetchAllVarieties();
      responseHandler.success(res, data, '所有品种数据获取成功');
    } catch (error) {
      console.error('获取所有品种数据失败:', error);
      responseHandler.error(res, '所有品种数据获取失败', 500);
    }
  }

  /**
   * 获取品种数据（保持向后兼容）
   */
  async getVarieties(req, res) {
    try {
      const data = await varietiesService.fetchVarieties();
      responseHandler.success(res, data, '数据获取成功');
    } catch (error) {
      console.error('获取品种数据失败:', error);
      responseHandler.error(res, '数据获取失败', 500);
    }
  }

  /**
   * 获取最近合约数据
   */
  async getRecentContracts(req, res) {
    try {
      const { variety, date } = req.body;
      const data = await varietiesService.fetchRecentContracts(variety, date);
      responseHandler.success(res, data, '最近合约数据获取成功');
    } catch (error) {
      console.error('获取最近合约数据失败:', error);
      responseHandler.error(res, '最近合约数据获取失败', 500);
    }
  }

  /**
   * 获取品种结构数据
   */
  async getVarietyStructure(req, res) {
    try {
      const { variety, code, broker_type } = req.body;
      const data = await varietiesService.fetchVarietyStructure(variety, code, broker_type);
      responseHandler.success(res, data, '品种结构数据获取成功');
    } catch (error) {
      console.error('获取品种结构数据失败:', error);
      responseHandler.error(res, '品种结构数据获取失败', 500);
    }
  }

  /**
   * 获取品种日期数据
   */
  async getVarietyDates(req, res) {
    try {
      const { variety } = req.body;
      const data = await varietiesService.fetchVarietyDates(variety);
      responseHandler.success(res, data, '品种日期数据获取成功');
    } catch (error) {
      console.error('获取品种日期数据失败:', error);
      responseHandler.error(res, '品种日期数据获取失败', 500);
    }
  }

  /**
   * 获取品种盈亏数据
   */
  async getVarietyProfitLoss(req, res) {
    try {
      const { variety, date1, date2 } = req.body;
      const data = await varietiesService.fetchVarietyProfitLoss(variety, date1, date2);
      responseHandler.success(res, data, '品种盈亏数据获取成功');
    } catch (error) {
      console.error('获取品种盈亏数据失败:', error);
      responseHandler.error(res, '品种盈亏数据获取失败', 500);
    }
  }
}

module.exports = new VarietiesController(); 