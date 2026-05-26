import React, { useState } from 'react';
import { FaUpload } from 'react-icons/fa';
import { MdTextFields, MdTableChart, MdBarChart } from 'react-icons/md';
import ChatInput from '../../components/features/ChatInput';
import MessageDisplay from '../../components/features/MessageDisplay';
import './Home.css';

const Home = () => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedMode, setSelectedMode] = useState('text');
    const [showUploadTrigger, setShowUploadTrigger] = useState(false);

    const handleMessageSent = (query, response) => {
        const userMessage = {
            type: 'user',
            text: query,
            timestamp: new Date().toISOString(),
        };

        const botMessage = response ? {
            type: 'bot',
            answer: response.data?.answer || response.message || 'No response received',
            results: response.data?.results || null,
            mode: response.data?.mode || selectedMode,
            visualization_data: response.data?.visualization_data || null,
            table_data: response.data?.table_data || null,
            timestamp: new Date().toISOString(),
        } : null;

        setMessages((prev) => {
            const newMessages = [...prev, userMessage];
            if (botMessage) newMessages.push(botMessage);
            return newMessages;
        });
    };

    const handleQueryLoading = (loading) => {
        setIsLoading(loading);
    };

    const modes = [
        { key: 'text', label: 'Text', Icon: MdTextFields },
        { key: 'table', label: 'Table', Icon: MdTableChart },
        { key: 'graph', label: 'Graph', Icon: MdBarChart },
    ];

    return (
        <div className="home-container">
            {/* Top Bar */}
            <div className="topbar">
                <div className="topbar-title">
                    <h2 className="topbar-heading">Smart Challan Assistant</h2>
                    <p className="topbar-sub">Indore Municipal Corporation</p>
                </div>
                <div className="topbar-actions">
                    <div className="mode-btn-group">
                        {modes.map(({ key, label, Icon }) => (
                            <button
                                key={key}
                                className={`mode-btn ${selectedMode === key ? 'active' : ''}`}
                                onClick={() => setSelectedMode(key)}
                            >
                                <Icon className="mode-btn-icon" />
                                {label}
                            </button>
                        ))}
                    </div>
                    <button
                        className="upload-excel-btn"
                        onClick={() => setShowUploadTrigger(true)}
                    >
                        <FaUpload className="upload-excel-icon" />
                        Upload Excel
                    </button>
                </div>
            </div>

            {/* Chat Area */}
            <div className="content-wrapper">
                {messages.length === 0 && !isLoading && (
                    <h1 className="greeting">What can I help with?</h1>
                )}
                <MessageDisplay messages={messages} isLoading={isLoading} />
                <ChatInput
                    onMessageSent={handleMessageSent}
                    onQueryLoading={handleQueryLoading}
                    selectedMode={selectedMode}
                    triggerUpload={showUploadTrigger}
                    onUploadTriggered={() => setShowUploadTrigger(false)}
                />
            </div>
        </div>
    );
};

export default Home;