import axios from 'axios';
import { API_BASE_URL, STORAGE_KEYS } from '../config/constants';

// Create axios instance
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - Add token to requests
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response) {
            // Server responded with error
            return Promise.reject(error.response.data);
        } else if (error.request) {
            // Request made but no response
            return Promise.reject({
                status: false,
                message: 'Network error. Please check your connection.'
            });
        } else {
            // Something else happened
            return Promise.reject({
                status: false,
                message: error.message
            });
        }
    }
);

// Auth API functions
export const authAPI = {
    // Request OTP
    requestOTP: async (email) => {
        return await apiClient.post('/auth/request-otp', { email });
    },

    // Verify OTP and login
    verifyOTP: async (email, otp) => {
        return await apiClient.post('/auth/verify-otp', { email, otp });
    },

    // Login with MPIN
    loginMPIN: async (email, mpin) => {
        return await apiClient.post('/auth/login-mpin', { email, mpin });
    },

    // Get user profile
    getProfile: async () => {
        return await apiClient.get('/auth/profile');
    },

    // Update user profile
    updateProfile: async (data) => {
        return await apiClient.put('/auth/profile', data);
    },

    // Set MPIN
    setMPIN: async () => {
        return await apiClient.post('/auth/set-mpin');
    },
};

// Agent API functions
export const agentAPI = {
    // Upload Excel file
    uploadExcel: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return await apiClient.post('/agent/upload-excel', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Query with natural language
    query: async (query, topK = 5, mode = 'text', tableName = null) => {
        const payload = { 
            query, 
            top_k: topK,
            mode: mode.toLowerCase() // 'text', 'graph', or 'table'
        };
        if (tableName) {
            payload.table_name = tableName;
        }
        return await apiClient.post('/agent/query', payload);
    },

    // List all uploaded files
    listFiles: async () => {
        return await apiClient.get('/agent/files');
    },

    // Delete a file
    deleteFile: async (fileId) => {
        return await apiClient.delete(`/agent/files/${fileId}`);
    },
};

export default apiClient;
