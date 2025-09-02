const fs = require('fs');
const path = require('path');

// 读取contracts.json文件
function decodeContracts() {
    try {
        // 读取文件
        const filePath = path.join(__dirname, 'contracts.json');
        const rawData = fs.readFileSync(filePath, 'utf8');
        
        // 解析JSON
        const data = JSON.parse(rawData);
        
        // 递归转换对象中的Unicode编码字符串
        function decodeUnicodeInObject(obj) {
            if (typeof obj === 'string') {
                // 将Unicode编码转换为真正的汉字
                return obj.replace(/\\u[\dA-Fa-f]{4}/g, function(match) {
                    return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
                });
            } else if (Array.isArray(obj)) {
                return obj.map(decodeUnicodeInObject);
            } else if (typeof obj === 'object' && obj !== null) {
                const result = {};
                for (const key in obj) {
                    result[decodeUnicodeInObject(key)] = decodeUnicodeInObject(obj[key]);
                }
                return result;
            }
            return obj;
        }
        
        // 转换数据
        const decodedData = decodeUnicodeInObject(data);
        
        // 将转换后的数据写回文件
        fs.writeFileSync(filePath, JSON.stringify(decodedData, null, 2), 'utf8');
        
        console.log('转码完成！已将Unicode编码的汉字转换为真正的汉字。');
        console.log('转换后的数据：');
        console.log(JSON.stringify(decodedData, null, 2));
        
    } catch (error) {
        console.error('转码过程中发生错误：', error.message);
    }
}

// 执行转码
decodeContracts();
