class ResponseHandler {
  /**
   * 成功响应
   */
  success(res, data = null, message = 'Success', statusCode = 200) {
    return res.status(statusCode).json({
      success: true,
      message,
      data,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 错误响应
   */
  error(res, message = 'Error', statusCode = 500, errorCode = null) {
    return res.status(statusCode).json({
      success: false,
      message,
      errorCode,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 验证错误响应
   */
  validationError(res, errors, message = '请求参数验证失败') {
    return res.status(400).json({
      success: false,
      message,
      errors,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 未授权响应
   */
  unauthorized(res, message = '未授权访问') {
    return res.status(401).json({
      success: false,
      message,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 禁止访问响应
   */
  forbidden(res, message = '禁止访问') {
    return res.status(403).json({
      success: false,
      message,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 资源未找到响应
   */
  notFound(res, message = '资源未找到') {
    return res.status(404).json({
      success: false,
      message,
      timestamp: new Date().toISOString()
    });
  }
}

module.exports = {
  responseHandler: new ResponseHandler()
}; 