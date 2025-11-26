import React, { useState } from 'react';
import ChatInput from '../../components/features/ChatInput';
import MessageDisplay from '../../components/features/MessageDisplay';
import './Home.css';

const Home = () => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleMessageSent = (query, response) => {
        // Add user message
        const userMessage = {
            type: 'user',
            text: query,
            timestamp: new Date().toISOString(),
        };

        // Add bot response if available
        const botMessage = response ? {
            type: 'bot',
            answer: response.data?.answer || response.message || 'No response received',
            results: response.data?.results || null,
            timestamp: new Date().toISOString(),
        } : null;

        setMessages((prev) => {
            const newMessages = [...prev, userMessage];
            if (botMessage) {
                newMessages.push(botMessage);
            }
            return newMessages;
        });
    };

    const handleQueryLoading = (loading) => {
        setIsLoading(loading);
    };

    return (
        <div className="home-container">
            <div className="branding-header">
                <div className="logo-container">
                    <img src="/logo-dark.png" alt="Shreshthaa Logo" className="brand-logo" />
                </div>
                <div className="brand-text">
                    <h2 className="brand-name">Shreshthaa</h2>
                    <p className="brand-subtitle">Powered by Smart City Development Ltd.</p>
                </div>
            </div>
            <div className="content-wrapper">
                {messages.length === 0 && !isLoading && (
                    <h1 className="greeting">What can I help with?</h1>
                )}
                <MessageDisplay messages={messages} isLoading={isLoading} />
                <ChatInput 
                    onMessageSent={handleMessageSent} 
                    onQueryLoading={handleQueryLoading}
                />
            </div>
        </div>
    );
};

export default Home;
