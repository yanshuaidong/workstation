// 新闻服务商配置
// 用于管理已对接的新闻能力提供商

const newsProvidersConfig = {
  // 东方财富新闻服务
  eastmoney: {
    name: '东方财富',
    // 支持的期货品种和新闻地址
    config: require('./eastmoneyNews.js'),
  }
  
  // 未来可以添加更多新闻服务商
  // 例如：
  // sina: {
  //   name: '新浪财经',
  //   config: require('./sinaNews.js'),
  // }
};

module.exports = newsProvidersConfig;