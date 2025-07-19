const express = require('express');
const router = express.Router();

// 导入控制器
const varietiesController = require('../controllers/varietiesController');

// 路由定义
router.post('/get-all-varieties', varietiesController.getAllVarieties);
router.post('/get-varieties', varietiesController.getVarieties);
router.post('/get-recent-contracts', varietiesController.getRecentContracts);
router.post('/get-variety-structure', varietiesController.getVarietyStructure);
router.post('/get-variety-dates', varietiesController.getVarietyDates);
router.post('/get-variety-profit-loss', varietiesController.getVarietyProfitLoss);

// 可以添加更多路由
// router.get('/health', (req, res) => {
//   res.json({ status: 'OK', timestamp: new Date().toISOString() });
// });

module.exports = router; 