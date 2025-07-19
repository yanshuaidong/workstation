require('dotenv').config();

const config = {
  // 服务器配置
  port: process.env.PORT || 3000,
  
  // 环境配置
  env: process.env.NODE_ENV || 'development',
  
  // 第三方API配置
  externalApi: {
    jiaoyikecha: {
      baseUrl: 'https://www.jiaoyikecha.com',
      varietiesEndpoint: '/ajax/all_varieties.php?v=92c571cf',
      headers: {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': process.env.JIAOYIKECHA_COOKIE || 'Hm_lvt_82e02aae42734877305ee2d72ac6e6ad=1750769230,1751543794; HMACCOUNT=B81D602E852D6233; PHPSESSID=99df676e5d2154b6576f09d79a1791d2; remember=55e535ee8f86c6589906d9f18f6acad3; Hm_lpvt_82e02aae42734877305ee2d72ac6e6ad=1752914787',
        'origin': 'https://www.jiaoyikecha.com',
        'priority': 'u=1, i',
        'referer': 'https://www.jiaoyikecha.com/',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
      }
    }
  },
  
  // CORS配置
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Origin', 'X-Requested-With', 'Content-Type', 'Accept', 'Authorization']
  }
};

module.exports = config; 