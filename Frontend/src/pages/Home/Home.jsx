import React, { useState } from 'react';
import ChatInput from '../../components/features/ChatInput';
import './Home.css';

const Home = () => {
    const [hasMessages, setHasMessages] = useState(false);

    const handleMessageSent = () => {
        setHasMessages(true);
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
            {!hasMessages && <h1 className="greeting">What can I help with?</h1>}
            <ChatInput onMessageSent={handleMessageSent} />
        </div>
    );
};

export default Home;
