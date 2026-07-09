// src/lib/axios.js
import axios from "axios";

// Determine environment (Vite injects these; `process` does not exist in the browser)
const isProduction = import.meta.env.PROD;
const isDevelopment = import.meta.env.DEV;

// Get API URL from environment variables with fallbacks
let BASE_URL = "";

// Priority: VITE_API_BASE_URL -> VITE_API_URL -> default based on environment
if (import.meta.env.VITE_API_BASE_URL) {
  BASE_URL = import.meta.env.VITE_API_BASE_URL;
} else if (import.meta.env.VITE_API_URL) {
  BASE_URL = import.meta.env.VITE_API_URL;
} else {
  // Default URLs based on environment
  if (isProduction) {
    // Production URL - assuming your app is at https://jamiikazini.com/
    BASE_URL = "https://jamiikazini.com/api/v1";
  } else {
    // Development URL
    BASE_URL = "http://localhost:8000/api/v1";
  }
}

// Ensure URL ends without trailing slash for consistency
BASE_URL = BASE_URL.replace(/\/$/, "");

console.log(`API Base URL: ${BASE_URL} (${isProduction ? 'Production' : 'Development'})`);

// Create axios instance with production-optimized settings
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  timeout: isProduction ? 30000 : 60000,
  maxRedirects: 5,
  maxContentLength: 50 * 1024 * 1024,
  validateStatus: function (status) {
    return status >= 200 && status < 300; // Only 2xx are success
  }
});

// Helper function to parse JWT tokens
const parseJwt = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Failed to parse JWT token:", e);
    return null;
  }
};

// Store rate limit info
let rateLimitInfo = {
  isLimited: false,
  limitUntil: 0,
  limitRemaining: null,
  limitReset: null
};

// Request queue for rate limiting
let requestQueue = [];
let isProcessingQueue = false;

// Process queued requests
const processQueue = async () => {
  if (isProcessingQueue || requestQueue.length === 0) return;
  
  isProcessingQueue = true;
  
  while (requestQueue.length > 0) {
    const requestConfig = requestQueue.shift();
    
    // Check if we're still rate limited
    if (rateLimitInfo.isLimited && Date.now() < rateLimitInfo.limitUntil) {
      // Re-add to front of queue
      requestQueue.unshift(requestConfig);
      break;
    }
    
    try {
      await api.request(requestConfig);
    } catch {
      // Error is handled by response interceptor
    }
    
    // Add small delay between requests
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  isProcessingQueue = false;
};

// Request interceptor: Add token and handle rate limiting
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = isProduction ? 500 : 1000;

api.interceptors.request.use(
  async (config) => {
    // Add authorization token
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add CSRF token for Django if available
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    // Add request ID for tracking
    config.headers['X-Request-ID'] = Date.now() + Math.random().toString(36).substr(2, 9);
    
    // Rate limiting check
    if (rateLimitInfo.isLimited && Date.now() < rateLimitInfo.limitUntil) {
      const waitTime = rateLimitInfo.limitUntil - Date.now();
      
      console.warn(`Rate limited: Queueing request. Wait ${Math.ceil(waitTime/1000)}s`);
      
      // Queue the request instead of rejecting it
      return new Promise((resolve, reject) => {
        requestQueue.push({
          ...config,
          resolve,
          reject
        });
        
        // Process queue after rate limit expires
        setTimeout(() => {
          rateLimitInfo.isLimited = false;
          processQueue();
        }, waitTime + 1000);
      });
    }
    
    // Add delay between requests to prevent rapid firing
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    
    if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
      await new Promise(resolve => 
        setTimeout(resolve, MIN_REQUEST_INTERVAL - timeSinceLastRequest)
      );
    }
    
    lastRequestTime = Date.now();
    
    // Log request in development
    if (isDevelopment) {
      console.log(`REQUEST: ${config.method?.toUpperCase()} ${config.url}`, config.params || '');
    }
    
    return config;
  },
  (error) => {
    console.error("Request interceptor error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor: Handle token refresh, rate limiting, and errors
api.interceptors.response.use(
  (response) => {
    // Update rate limit info from headers if available
    if (response.headers['x-ratelimit-remaining']) {
      rateLimitInfo.limitRemaining = parseInt(response.headers['x-ratelimit-remaining']);
      rateLimitInfo.limitReset = response.headers['x-ratelimit-reset'];
      
      if (rateLimitInfo.limitRemaining <= 1) {
        console.warn(`Approaching rate limit: ${rateLimitInfo.limitRemaining} requests remaining`);
      }
    }
    
    // Reset rate limiting on successful response
    rateLimitInfo.isLimited = false;
    
    // Log response in development
    if (isDevelopment) {
      console.log(`RESPONSE: ${response.status} ${response.config.url}`, response.data);
    }
    
    // Process queued requests
    if (requestQueue.length > 0 && !rateLimitInfo.isLimited) {
      setTimeout(processQueue, 100);
    }
    
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Log error in development
    if (isDevelopment) {
      console.error(`ERROR: ${error.response?.status || 'Network'} ${error.config?.url}`, error.response?.data || error.message);
    }
    
    // Handle network errors
    if (!error.response) {
      console.error("Network error:", error.message);
      return Promise.reject(error);
    }
    
    // Handle 401 for login - DON'T try to refresh token
    if (error.response?.status === 401 && originalRequest?.url?.includes('/security/login/')) {
      return Promise.reject(error);
    }
    
    // Handle 404 for login - user not found
    if (error.response?.status === 404 && originalRequest?.url?.includes('/security/login/')) {
      return Promise.reject(error);
    }
    
    // Handle 429 Rate Limiting
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : 30000;
      
      rateLimitInfo.isLimited = true;
      rateLimitInfo.limitUntil = Date.now() + waitTime;
      
      console.warn(`Rate limited. Wait ${waitTime/1000} seconds before retrying.`);
      
      if (originalRequest && !originalRequest._retry) {
        originalRequest._retry = true;
        
        setTimeout(() => {
          console.log("Auto-retrying rate limited request...");
          rateLimitInfo.isLimited = false;
          return api(originalRequest);
        }, waitTime + 1000);
      }
      
      return Promise.reject(error);
    }
    
    // Handle 401 Unauthorized - Token Refresh (for non-login requests)
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
          throw new Error("No refresh token");
        }
        
        const decoded = parseJwt(refreshToken);
        const now = Date.now() / 1000;
        
        if (!decoded?.exp || decoded.exp < now) {
          throw new Error("Refresh token expired");
        }
        
        const refreshResponse = await axios({
          method: 'post',
          url: `${BASE_URL}/security/token/refresh/`,
          data: { refresh: refreshToken },
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        const newAccessToken = refreshResponse.data.access;
        localStorage.setItem("access_token", newAccessToken);
        
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);
        
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        
        window.location.href = "/security/login";
        
        return Promise.reject(refreshError);
      }
    }
    
    // Handle 500 errors
    if (error.response?.status >= 500) {
      console.error(`Server Error ${error.response.status}:`, error.response.data?.detail || error.message);
    }
    
    // Handle 400 errors
    if (error.response?.status === 400) {
      console.error("Validation error:", error.response.data);
    }
    
    // Handle 403 errors
    if (error.response?.status === 403) {
      console.error("Permission denied:", error.response.data?.detail || error.message);
    }
    
    return Promise.reject(error);
  }
);

// Export utility functions
export const checkRateLimitStatus = () => {
  if (rateLimitInfo.isLimited && Date.now() < rateLimitInfo.limitUntil) {
    const waitTime = rateLimitInfo.limitUntil - Date.now();
    return {
      isLimited: true,
      waitSeconds: Math.ceil(waitTime / 1000),
      waitUntil: new Date(rateLimitInfo.limitUntil),
      remaining: rateLimitInfo.limitRemaining,
      reset: rateLimitInfo.limitReset
    };
  }
  return { 
    isLimited: false,
    remaining: rateLimitInfo.limitRemaining,
    reset: rateLimitInfo.limitReset
  };
};

export const clearRateLimit = () => {
  rateLimitInfo.isLimited = false;
  rateLimitInfo.limitUntil = 0;
  requestQueue = [];
  console.log("Rate limit cleared");
};

export const getApiBaseUrl = () => BASE_URL;
export const getEnvironment = () => isProduction ? 'production' : 'development';

export default api;