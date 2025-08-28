const fs = require('fs');
const path = require('path');

// 读取原始数据文件
const filePath = path.join(__dirname, 'jishu.md');
const raw = fs.readFileSync(filePath, 'utf-8').split(/\r?\n/).filter(Boolean);

// 跳过前8行表头，后面每8行为一组
// 原始数据顺序：时间、收盘价、涨跌幅(%)、成交量、持仓量、日增仓、最高、最低
// 目标表头顺序：时间、收盘价、最高价、最低价、涨跌幅(%)、成交量、持仓量、日增仓
const header = ['时间', '收盘价','最高价', '最低价', '涨跌幅(%)', '成交量', '持仓量', '日增仓'];
const rows = [];

for (let i = 8; i < raw.length; i += 8) {
  const rawRow = raw.slice(i, i + 8);
  if (rawRow.length === 8) {
    // 重新排列数据顺序：[时间, 收盘价, 最高, 最低, 涨跌幅, 成交量, 持仓量, 日增仓]
    const reorderedRow = [
      rawRow[0], // 时间
      rawRow[1], // 收盘价
      rawRow[6], // 最高价
      rawRow[7], // 最低价
      rawRow[2], // 涨跌幅(%)
      rawRow[3], // 成交量
      rawRow[4], // 持仓量
      rawRow[5]  // 日增仓
    ];
    rows.push(reorderedRow);
  }
}

// 生成Markdown表格
let table = `|${header.join('|')}|\n`;
rows.forEach(r => {
  table += `|${r.join('|')}|\n`;
});

// 覆盖写回jishu.md
fs.writeFileSync(filePath, table, 'utf-8');

console.log('转换完成，已覆盖写回jishu.md');
