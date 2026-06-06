import axios from "axios";
import { ElMessage } from "element-plus";

const http = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  timeout: 10000
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestId = error?.response?.data?.request_id;
    const message =
      error?.code === "ECONNABORTED"
        ? "请求超时，请稍后重试。"
        : error?.response?.data?.detail ||
          error?.message ||
          "请求失败，请稍后重试。";

    ElMessage.error(requestId ? `${message}（请求ID: ${requestId}）` : message);
    return Promise.reject(error);
  }
);

export default http;
