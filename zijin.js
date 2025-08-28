const fs = require('fs');

// 读取文件内容
let content = fs.readFileSync('temp.md', 'utf-8');

// 处理每一行，过滤空行
let lines = content.trim().split('\n').filter(line => line.trim() !== '');

function formatNum(num) {
  const n = Math.abs(Number(num));
  const y = (n / 100000000).toFixed(2);
  if (Number(num) > 0) {
    return `净多${y}亿`;
  } else {
    return `净空${y}亿`;
  }
}

// 如果有数据行
if (lines.length >= 2) {
  // 第一行是表头
  const headerLine = lines[0];
  const headers = headerLine.trim().split(/\s+/);
  
  // 数据行（从第二行开始）
  const dataLines = lines.slice(1);
  
  // 逆序排列数据行（日期近的在前）
  const sortedDataLines = dataLines.reverse();
  
  // 构建表格
  const tableLines = [];
  
  // 表头行
  const tableHeader = `| 日期 |${headers.join('|')}|`;
  tableLines.push(tableHeader);
  
  // 数据行
  sortedDataLines.forEach(line => {
    const parts = line.trim().split(/\s+/);
    const date = parts[0];
    const nums = parts.slice(1);
    const formatted = nums.map(formatNum);
    const tableRow = `|${date}|${formatted.join('|')}|`;
    tableLines.push(tableRow);
  });
  
  // 写入文件
  fs.writeFileSync('temp.md', tableLines.join('\n') + '\n');
} else {
  console.log('数据格式不正确，需要至少包含表头和一行数据');
}
