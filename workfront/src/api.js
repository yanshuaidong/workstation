// API 接口定义
const BASE_URL_3000 = 'http://localhost:3000/api';
const BASE_URL_5000 = 'http://localhost:5000/api';

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

// 5000端口的接口
export const testApi5000 = `${BASE_URL_5000}/test`;
export const getUsersApi5000 = `${BASE_URL_5000}/users`;
export const createUserApi5000 = `${BASE_URL_5000}/users`;

// 期货相关接口 (5000端口)
export const getFuturesContractsApi = `${BASE_URL_5000}/futures/contracts`;
export const getFuturesHistoryApi = `${BASE_URL_5000}/futures/history`;
export const getFuturesPeriodsApi = `${BASE_URL_5000}/futures/periods`;
export const refreshFuturesContractsApi = `${BASE_URL_5000}/futures/refresh-contracts`;

// 旧版本兼容（相对路径）
export const getUsersApi = '/api/users'
export const createUserApi = '/api/users'
export const updateUserApi = '/api/users'
export const deleteUserApi = '/api/users'

// 导出端口配置，方便组件使用
export const API_PORTS = {
  PORT_3000: BASE_URL_3000,
  PORT_5000: BASE_URL_5000
} 