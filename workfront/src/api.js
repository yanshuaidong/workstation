// API 接口定义
const BASE_URL = 'http://localhost:3000/api';

// 导出所有API接口路径
export const getAllVarietiesApi = `${BASE_URL}/get-all-varieties`;
export const getVarietiesApi = `${BASE_URL}/get-varieties`;
export const getRecentContractsApi = `${BASE_URL}/get-recent-contracts`;
export const getVarietyStructureApi = `${BASE_URL}/get-variety-structure`;
export const getVarietyDatesApi = `${BASE_URL}/get-variety-dates`;
export const getVarietyProfitLossApi = `${BASE_URL}/get-variety-profit-loss`;

// 也可以单独导出每个路径
export const getUsersApi = '/api/users'
export const createUserApi = '/api/users'
export const updateUserApi = '/api/users'
export const deleteUserApi = '/api/users' 