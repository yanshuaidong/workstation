const express = require('express');
const router = express.Router();

// 导入控制器
const varietiesController = require('../controllers/varietiesController');
const openctpController = require('../controllers/openctpController');
const newsController = require('../controllers/newsController');

// 原有的品种相关路由
router.post('/get-all-varieties', varietiesController.getAllVarieties);
router.post('/get-varieties', varietiesController.getVarieties);
router.post('/get-recent-contracts', varietiesController.getRecentContracts);
router.post('/get-variety-structure', varietiesController.getVarietyStructure);
router.post('/get-variety-dates', varietiesController.getVarietyDates);
router.post('/get-variety-profit-loss', varietiesController.getVarietyProfitLoss);

// 新增的 OpenCTP 接口路由
router.post('/get-markets', openctpController.getMarkets);
router.post('/get-products', openctpController.getProducts);
router.post('/get-instruments', openctpController.getInstruments);
router.post('/get-prices', openctpController.getPrices);

// 新闻相关路由
router.post('/get-news-providers', newsController.getNewsProviders);
router.post('/get-varieties-by-provider', newsController.getVarietiesByProvider);
router.post('/get-futures-news', newsController.getFuturesNews);

// 可以添加更多路由
// router.get('/health', (req, res) => {
//   res.json({ status: 'OK', timestamp: new Date().toISOString() });
// });

module.exports = router; 