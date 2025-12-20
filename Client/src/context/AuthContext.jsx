import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';
import { STORAGE_KEYS } from '../config/constants';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is already logged in
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);

        if (token && storedUser) {
            setIsAuthenticated(true);
            setUser(JSON.parse(storedUser));
        }
        setLoading(false);
    }, []);

    const login = async (email, otp) => {
        try {
            const response = await authAPI.verifyOTP(email, otp);

            if (response.status) {
                const { token, ...userData } = response.data;

                // Store token and user data
                localStorage.setItem(STORAGE_KEYS.TOKEN, token);
                localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));

                setIsAuthenticated(true);
                setUser(userData);

                return { success: true };
            } else {
                return { success: false, message: response.message };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                message: error.message || 'Login failed. Please try again.'
            };
        }
    };

    const logout = () => {
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER);
        setIsAuthenticated(false);
        setUser(null);
    };

    const updateProfile = async (newData) => {
        try {
            const response = await authAPI.updateProfile(newData);

            if (response.status) {
                const updatedUser = { ...user, ...response.data };
                setUser(updatedUser);
                localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updatedUser));
                return { success: true };
            } else {
                return { success: false, message: response.message };
            }
        } catch (error) {
            console.error('Update profile error:', error);
            return {
                success: false,
                message: error.message || 'Failed to update profile.'
            };
        }
    };

    const requestOTP = async (email) => {
        try {
            const response = await authAPI.requestOTP(email);

            if (response.status) {
                return { success: true, message: response.message };
            } else {
                return { success: false, message: response.message };
            }
        } catch (error) {
            console.error('Request OTP error:', error);
            return {
                success: false,
                message: error.message || 'Failed to send OTP.'
            };
        }
    };

    const loginMPIN = async (email, mpin) => {
        try {
            const response = await authAPI.loginMPIN(email, mpin);

            if (response.status) {
                const { token, ...userData } = response.data;

                // Store token and user data
                localStorage.setItem(STORAGE_KEYS.TOKEN, token);
                localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));

                setIsAuthenticated(true);
                setUser(userData);

                return { success: true };
            } else {
                return { success: false, message: response.message };
            }
        } catch (error) {
            console.error('MPIN Login error:', error);
            return {
                success: false,
                message: error.message || 'MPIN login failed. Please try again.'
            };
        }
    };

    return (
        <AuthContext.Provider value={{
            isAuthenticated,
            user,
            loading,
            login,
            loginMPIN,
            logout,
            updateProfile,
            requestOTP
        }}>
            {children}
        </AuthContext.Provider>
    );
};
