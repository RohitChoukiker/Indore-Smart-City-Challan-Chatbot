import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const storedAuth = localStorage.getItem('isAuthenticated');
        const storedUser = localStorage.getItem('user');
        if (storedAuth === 'true') {
            setIsAuthenticated(true);
            setUser(storedUser ? JSON.parse(storedUser) : {
                name: 'Test User',
                email: 'Test@gmail.com',
                department: 'Engineering',
                designation: 'Developer'
            });
        }
    }, []);

    const login = (method, credentials) => {
        console.log(`Logging in via ${method}`, credentials);
        localStorage.setItem('isAuthenticated', 'true');
        const userData = {
            name: 'Test User',
            email: credentials.email || 'User',
            department: 'Engineering',
            designation: 'Developer'
        };
        localStorage.setItem('user', JSON.stringify(userData));
        setIsAuthenticated(true);
        setUser(userData);
        return true;
    };

    const logout = () => {
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setUser(null);
    };

    const updateProfile = (newData) => {
        const updatedUser = { ...user, ...newData };
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, user, login, logout, updateProfile }}>
            {children}
        </AuthContext.Provider>
    );
};
