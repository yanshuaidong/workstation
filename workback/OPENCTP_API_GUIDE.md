# OpenCTP 接口使用指南

本文档描述了新增的四个 OpenCTP 数据字典接口的使用方法。

## 接口概览

所有接口都使用 POST 方法，基础 URL 为 `http://localhost:3000/api`

### 1. 获取市场数据
**接口地址**: `/get-markets`
**请求方法**: POST
**描述**: 获取交易市场信息

#### 请求参数
```json
{
  "areas": "China"  // 可选，国家/地区，多个值用逗号分隔，如 "China,USA"
}
```

#### 示例请求
```bash
curl -X POST http://localhost:3000/api/get-markets \
  -H "Content-Type: application/json" \
  -d '{"areas": "China"}'
```

### 2. 获取品种数据
**接口地址**: `/get-products`
**请求方法**: POST
**描述**: 获取金融产品品种信息

#### 请求参数
```json
{
  "types": "futures",        // 可选，商品类型，如 stock、bond、fund、futures、option
  "areas": "China",          // 可选，国家/地区
  "markets": "SHFE,CFFEX",   // 可选，交易所列表
  "products": "au,rb,IF"     // 可选，品种列表
}
```


{
  "rsp_code": 0,
  "rsp_message": "succeed",
  "data": [
    {
      "ExchangeID": "BSE",
      "ExchangeName": "北京证券交易所",
      "TimeZone": 8,
      "ShortName": "BSE",
      "Area": "China"
    },
    {
      "ExchangeID": "CFFEX",
      "ExchangeName": "中国金融期货交易所",
      "TimeZone": 8,
      "ShortName": "CFFEX",
      "Area": "China"
    }
  ]
}


#### 示例请求
```bash
curl -X POST http://localhost:3000/api/get-products \
  -H "Content-Type: application/json" \
  -d '{"types": "futures", "markets": "SHFE,CFFEX"}'
```

### 3. 获取合约数据
**接口地址**: `/get-instruments`
**请求方法**: POST
**描述**: 获取金融合约信息

#### 请求参数
```json
{
  "types": "futures",        // 可选，商品类型
  "areas": "China",          // 可选，国家/地区
  "markets": "SHFE,CFFEX",   // 可选，交易所列表
  "products": "au,rb,IF,IM"  // 可选，品种列表
}
```
{
  "rsp_code": 0,
  "rsp_message": "succeed",
  "data": [
    {
      "ExchangeID": "SHFE",
      "ProductID": "ag",
      "ProductName": "白银",
      "ProductClass": "1"
    },
    {
      "ExchangeID": "SHFE",
      "ProductID": "au",
      "ProductName": "黄金",
      "ProductClass": "1"
    }
  ]
}




#### 示例请求
```bash
curl -X POST http://localhost:3000/api/get-instruments \
  -H "Content-Type: application/json" \
  -d '{"types": "futures", "markets": "SHFE,CFFEX", "products": "au,rb,IF,IM"}'
```

### 4. 获取价格数据
**接口地址**: `/get-prices`
**请求方法**: POST
**描述**: 获取实时价格信息

#### 请求参数
```json
{
  "types": "futures",        // 可选，商品类型
  "areas": "China",          // 可选，国家/地区
  "markets": "SHFE,CFFEX",   // 可选，交易所列表
  "products": "au,rb,IF,IM"  // 可选，品种列表
}
```

{
  "rsp_code": 0,
  "rsp_message": "succeed",
  "data": [
    {
      "ExchangeID": "CFFEX",
      "InstrumentID": "IF2505",
      "InstrumentName": "股指2505",
      "ProductClass": "1",
      "VolumeMultiple": 300,
      "PriceTick": 0.2,
      "LongMarginRatioByMoney": 0.12,
      "ShortMarginRatioByMoney": 0.12,
      "OpenDate": "2025-03-24",
      "ExpireDate": "2025-05-16"
    }
  ]
}


#### 示例请求
```bash
curl -X POST http://localhost:3000/api/get-prices \
  -H "Content-Type: application/json" \
  -d '{"types": "futures", "markets": "SHFE,CFFEX", "products": "au,rb,IF,IM"}'
```

## 参数说明

### 通用参数
- **types**: 商品类型
  - `stock`: 股票
  - `bond`: 债券
  - `fund`: 基金
  - `futures`: 期货（注意是复数）
  - `option`: 期权
  - 多个值用逗号分隔

- **areas**: 国家/地区
  - `China`: 中国
  - `USA`: 美国
  - `UK`: 英国
  - `Singapore`: 新加坡
  - 多个值用逗号分隔

- **markets**: 交易所代码
  - `SHFE`: 上海期货交易所
  - `CFFEX`: 中国金融期货交易所
  - `SSE`: 上海证券交易所
  - `SZSE`: 深圳证券交易所
  - 多个值用逗号分隔

- **products**: 品种代码
  - `au`: 黄金
  - `rb`: 螺纹钢
  - `TA`: PTA
  - `IF`: 沪深300指数期货
  - 多个值用逗号分隔

## 响应格式

{
  "rsp_code": 0,
  "rsp_message": "succeed",
  "data": [
    {
      "ExchangeID": "SHFE",
      "InstrumentID": "ag2505",
      "ProductID": "ag",
      "ProductClass": "1",
      "LastPrice": 8160,
      "Volume": 0,
      "Turnover": 0,
      "OpenInterest": 5216,
      "PreClosePrice": 8160,
      "UpperLimitPrice": 9037,
      "LowerLimitPrice": 7246
    }
  ]
}


所有接口都返回统一的响应格式：

```json
{
  "success": true,
  "message": "数据获取成功",
  "data": {
    // 具体的响应数据
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```



## 错误处理

当请求失败时，会返回错误信息：

```json
{
  "success": false,
  "message": "错误描述",
  "error": "详细错误信息",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## 注意事项

1. 所有参数都是可选的，不传参数时会获取所有可用数据
2. 多个值之间用英文逗号分隔，不要有空格
3. 参数值区分大小写
4. 接口调用频率建议控制在合理范围内 