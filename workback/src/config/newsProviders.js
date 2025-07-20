// 新闻提供商配置
const newsProviders = [
  {
    id: 'eastmoney',
    name: '东方财富',
    description: '东方财富期货新闻资讯',
    enabled: true,
    supported_varieties: ['金', '银', '铜', '铝'] // 对应 eastmoneyNews.js 中的品种
  }
  // 可以扩展其他新闻提供商
  // {
  //   id: 'sina',
  //   name: '新浪财经',
  //   description: '新浪财经期货资讯',
  //   enabled: false,
  //   supported_varieties: []
  // }
];

module.exports = newsProviders;