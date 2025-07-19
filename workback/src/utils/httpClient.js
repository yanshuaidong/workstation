class HttpClient {
  /**
   * GET请求
   */
  async get(url, options = {}) {
    try {
      const response = await fetch(url, {
        method: 'GET',
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`GET请求失败: ${error.message}`);
    }
  }

  /**
   * POST请求
   */
  async post(url, data = null, options = {}) {
    try {
      let body = null;
      let defaultHeaders = {};

      if (data) {
        // 如果data是字符串（表单数据），直接使用
        if (typeof data === 'string') {
          body = data;
          defaultHeaders['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
        } else {
          // 否则JSON序列化
          body = JSON.stringify(data);
          defaultHeaders['Content-Type'] = 'application/json';
        }
      }

      const response = await fetch(url, {
        method: 'POST',
        body: body,
        headers: {
          ...defaultHeaders,
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`POST请求失败: ${error.message}`);
    }
  }

  /**
   * PUT请求
   */
  async put(url, data, options = {}) {
    try {
      const response = await fetch(url, {
        method: 'PUT',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`PUT请求失败: ${error.message}`);
    }
  }

  /**
   * DELETE请求
   */
  async delete(url, options = {}) {
    try {
      const response = await fetch(url, {
        method: 'DELETE',
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`DELETE请求失败: ${error.message}`);
    }
  }
}

module.exports = new HttpClient(); 