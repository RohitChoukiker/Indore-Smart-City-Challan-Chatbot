import React from 'react';
import ChatInput from '../../components/features/ChatInput';
import './Home.css';

const Home = () => {
    return (
        <div className="home-container">
            <div className="branding-header">
                <h2 className="brand-name">Shreshtha</h2>
                <p className="brand-subtitle">Powered by Smart City Development Ltd.</p>
            </div>
            <h1 className="greeting">What can I help with?</h1>
            <ChatInput />
        </div>
    );
};

export default Home;
