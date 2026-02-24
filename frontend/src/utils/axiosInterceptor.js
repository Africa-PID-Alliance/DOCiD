import axios from 'axios';
import { updateAccessToken, logout } from '../redux/slices/authSlice';

let store;

export const injectStore = (_store) => {
  store = _store;
};

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// Request interceptor to attach JWT token to outgoing requests
axios.interceptors.request.use(
  (config) => {
    if (store) {
      const state = store.getState();
      const accessToken = state.auth?.user?.accessToken;
      if (accessToken && !config.headers['Authorization']) {
        config.headers['Authorization'] = `Bearer ${accessToken}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling 401 errors and refreshing tokens
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried refreshing yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = 'Bearer ' + token;
            return axios(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const state = store.getState();
      const refreshToken = state.auth?.user?.refreshToken;

      if (!refreshToken) {
        // No refresh token available, logout
        store.dispatch(logout());
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        // Call the refresh token API
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken,
        });

        const { access_token } = response.data;

        // Update the access token in Redux store
        store.dispatch(updateAccessToken({ accessToken: access_token }));

        // Update the authorization header for the original request
        originalRequest.headers['Authorization'] = 'Bearer ' + access_token;

        // Process all queued requests with the new token
        processQueue(null, access_token);

        isRefreshing = false;

        // Retry the original request
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh token failed, logout user
        processQueue(refreshError, null);
        store.dispatch(logout());
        isRefreshing = false;

        // Redirect to login page if in browser
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
