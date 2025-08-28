const https = require('https');
const querystring = require('querystring');
const fs = require('fs');
const path = require('path');

// 配置参数
const config = {
  // 基础URL配置
  baseUrl: 'https://www.jiaoyikecha.com',
  endpoint: '/ajax/sub_brokers.php',
  version: '8ee341d0',
  
  // 请求头配置
  headers: {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.jiaoyikecha.com',
    'priority': 'u=1, i',
    'referer': 'https://www.jiaoyikecha.com/',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'
  },
  
  // Cookie配置（可根据需要更新）
  cookies: {
    'HMACCOUNT': 'B81D602E852D6233',
    'PHPSESSID': '99df676e5d2154b6576f09d79a1791d2',
    'Hm_lvt_82e02aae42734877305ee2d72ac6e6ad': '1754184074',
    'Hm_lpvt_82e02aae42734877305ee2d72ac6e6ad': '1755004343'
  }
};

/**
 * 从MD文件读取券商列表
 * @param {string} filePath MD文件路径
 * @returns {string[]} 券商名称数组
 */
function readBrokersFromMd(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    const brokers = [];
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      // 跳过空行、标题行（以#开头）和其他格式行
      if (trimmedLine && !trimmedLine.startsWith('#') && !trimmedLine.startsWith('-')) {
        brokers.push(trimmedLine);
      }
    }
    
    return brokers;
  } catch (error) {
    console.error(`读取MD文件失败: ${error.message}`);
    return [];
  }
}

/**
 * 发送请求到交易客查接口
 * @param {string[]} brokers 券商名称数组
 * @param {Object} customConfig 自定义配置，会覆盖默认配置
 * @returns {Promise} 返回Promise对象
 */
function requestSubBrokers(brokers, customConfig = {}) {
  // 合并配置
  const finalConfig = {
    ...config,
    ...customConfig,
    headers: { ...config.headers, ...(customConfig.headers || {}) },
    cookies: { ...config.cookies, ...(customConfig.cookies || {}) }
  };
  
  // 构建URL
  const url = `${finalConfig.baseUrl}${finalConfig.endpoint}?v=${finalConfig.version}`;
  
  // 构建Cookie字符串
  const cookieString = Object.entries(finalConfig.cookies)
    .map(([key, value]) => `${key}=${value}`)
    .join('; ');
  
  // 构建POST数据 - 支持多个券商
  const postData = querystring.stringify({
    'brokers[]': brokers
  });
  
  // 设置请求头
  const headers = {
    ...finalConfig.headers,
    'cookie': cookieString,
    'content-length': Buffer.byteLength(postData)
  };
  
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 443,
      path: urlObj.pathname + urlObj.search,
      method: 'POST',
      headers: headers
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: jsonData,
            brokers: brokers
          });
        } catch (error) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: data,
            brokers: brokers
          });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    // 发送POST数据
    req.write(postData);
    req.end();
  });
}

/**
 * 主函数：读取MD文件并查询券商信息
 * @param {string} mdFilePath MD文件路径，默认为当前目录下的guanzhu.md
 */
async function queryBrokersFromMd(mdFilePath = './guanzhu.md') {
  try {
    console.log(`正在读取券商列表文件: ${mdFilePath}`);
    
    // 读取券商列表
    const brokers = readBrokersFromMd(mdFilePath);
    
    if (brokers.length === 0) {
      console.log('未找到有效的券商名称，请检查MD文件格式');
      return;
    }
    
    console.log(`找到 ${brokers.length} 个券商:`, brokers);
    console.log('正在查询券商信息...');
    
    // 发送请求
    const result = await requestSubBrokers(brokers);
    
    console.log('查询结果:');
    console.log(`状态码: ${result.statusCode}`);
    console.log(`查询券商: ${result.brokers.join(', ')}`);
    console.log('响应数据:', JSON.stringify(result.data, null, 2));
    
    return result;
    
  } catch (error) {
    console.error('查询失败:', error);
    throw error;
  }
}

// 如果直接运行此文件，则执行主函数
if (require.main === module) {
  const mdFilePath = process.argv[2] || './guanzhu.md';
  queryBrokersFromMd(mdFilePath);
}

// 导出函数供其他模块使用
module.exports = {
  requestSubBrokers,
  readBrokersFromMd,
  queryBrokersFromMd,
  config
};
