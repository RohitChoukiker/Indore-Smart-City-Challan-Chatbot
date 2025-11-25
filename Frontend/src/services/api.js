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

export default apiClient;
