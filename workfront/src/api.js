// API 接口定义
const BASE_URL_3000 = 'http://localhost:3000/api';
const BASE_URL_7001 = 'http://localhost:7001/api';
const BASE_URL_7002 = 'http://localhost:7002/api';

// 3000端口的接口
export const getAllVarietiesApi = `${BASE_URL_3000}/get-all-varieties`;
export const getVarietiesApi = `${BASE_URL_3000}/get-varieties`;
export const getRecentContractsApi = `${BASE_URL_3000}/get-recent-contracts`;
export const getVarietyStructureApi = `${BASE_URL_3000}/get-variety-structure`;
export const getVarietyDatesApi = `${BASE_URL_3000}/get-variety-dates`;
export const getVarietyProfitLossApi = `${BASE_URL_3000}/get-variety-profit-loss`;

// OpenCTP 接口 (3000端口)
export const getMarketsApi = `${BASE_URL_3000}/get-markets`;
export const getProductsApi = `${BASE_URL_3000}/get-products`;
export const getInstrumentsApi = `${BASE_URL_3000}/get-instruments`;
export const getPricesApi = `${BASE_URL_3000}/get-prices`;

// 7001端口的接口
export const testApi7001 = `${BASE_URL_7001}/test`;
export const getUsersApi7001 = `${BASE_URL_7001}/users`;
export const createUserApi7001 = `${BASE_URL_7001}/users`;

// 期货相关接口 (7001端口)
export const getFuturesContractsApi = `${BASE_URL_7001}/futures/contracts`;
export const getFuturesHistoryApi = `${BASE_URL_7001}/futures/history`;
export const getFuturesPeriodsApi = `${BASE_URL_7001}/futures/periods`;
export const refreshFuturesContractsApi = `${BASE_URL_7001}/futures/refresh-contracts`;

// 期货数据更新系统接口 (7002端口) - 新版本
export const getSettingsApi = `${BASE_URL_7002}/settings`;
export const updateSettingsApi = `${BASE_URL_7002}/settings`;
export const updateContractsListApi = `${BASE_URL_7002}/contracts/update-list`;
export const getContractsListApi = `${BASE_URL_7002}/contracts/list`;
export const getListUpdateLogApi = `${BASE_URL_7002}/contracts/list-update-log`;
export const updateAllHistoryApi = `${BASE_URL_7002}/history/update-all`;
export const retrySingleHistoryApi = `${BASE_URL_7002}/history/retry-single`;
export const getHistoryLogsApi = `${BASE_URL_7002}/history/logs`;
export const getHistoryDataApi = `${BASE_URL_7002}/history/data`;

// 旧版本兼容（相对路径）
export const getUsersApi = '/api/users'
export const createUserApi = '/api/users'
export const updateUserApi = '/api/users'
export const deleteUserApi = '/api/users'

// 导出端口配置，方便组件使用
export const API_PORTS = {
  PORT_3000: BASE_URL_3000,
  PORT_7001: BASE_URL_7001,
  PORT_7002: BASE_URL_7002
} 