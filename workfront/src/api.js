// API 接口定义
// const BASE_URL_3000 = 'http://localhost:3000/api';  // 暂时注释不用
// const BASE_URL_7001 = 'http://localhost:7001/api';  // 暂时注释不用
const BASE_URL_API_A = '/api-a';  // 使用代理转发到7001端口

// 3000端口的接口 - 暂时注释不用
// export const getAllVarietiesApi = `${BASE_URL_3000}/get-all-varieties`;
// export const getVarietiesApi = `${BASE_URL_3000}/get-varieties`;
// export const getRecentContractsApi = `${BASE_URL_3000}/get-recent-contracts`;
// export const getVarietyStructureApi = `${BASE_URL_3000}/get-variety-structure`;
// export const getVarietyDatesApi = `${BASE_URL_3000}/get-variety-dates`;
// export const getVarietyProfitLossApi = `${BASE_URL_3000}/get-variety-profit-loss`;

// OpenCTP 接口 - 暂时注释不用
// export const getMarketsApi = `${BASE_URL_3000}/get-markets`;
// export const getProductsApi = `${BASE_URL_3000}/get-products`;
// export const getInstrumentsApi = `${BASE_URL_3000}/get-instruments`;
// export const getPricesApi = `${BASE_URL_3000}/get-prices`;

// 7001端口的接口 - 暂时注释不用
// export const testApi7001 = `${BASE_URL_7001}/test`;
// export const getUsersApi7001 = `${BASE_URL_7001}/users`;
// export const createUserApi7001 = `${BASE_URL_7001}/users`;

// 期货相关接口 (现在使用 /api-a/ 代理)
export const getFuturesContractsApi = `${BASE_URL_API_A}/futures/contracts`;
export const getFuturesHistoryApi = `${BASE_URL_API_A}/futures/history`;
export const getFuturesPeriodsApi = `${BASE_URL_API_A}/futures/periods`;
export const refreshFuturesContractsApi = `${BASE_URL_API_A}/futures/refresh-contracts`;

// 期货数据更新系统接口 (现在使用7001端口，通过 /api-a/ 代理)
export const getSettingsApi = `${BASE_URL_API_A}/settings`;
export const updateSettingsApi = `${BASE_URL_API_A}/settings`;
export const updateContractsListApi = `${BASE_URL_API_A}/contracts/update-list`;
export const getContractsListApi = `${BASE_URL_API_A}/contracts/list`;
export const getListUpdateLogApi = `${BASE_URL_API_A}/contracts/list-update-log`;
export const updateAllHistoryApi = `${BASE_URL_API_A}/history/update-all`;
export const retrySingleHistoryApi = `${BASE_URL_API_A}/history/retry-single`;
export const getHistoryLogsApi = `${BASE_URL_API_A}/history/logs`;
export const getHistoryDataApi = `${BASE_URL_API_A}/history/data`;

// 分时行情数据接口
export const getIntradayContractsApi = `${BASE_URL_API_A}/intraday/contracts`;
export const getIntradayDataApi = `${BASE_URL_API_A}/intraday/data`;


// 导出端口配置，方便组件使用
export const API_PORTS = {
  // PORT_3000: BASE_URL_3000,  // 暂时注释不用
  // PORT_7001: BASE_URL_7001,  // 暂时注释不用
  API_A: BASE_URL_API_A  // 使用代理转发
} 