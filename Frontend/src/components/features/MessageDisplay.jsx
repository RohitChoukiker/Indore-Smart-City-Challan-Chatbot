import React from 'react';
import { FaUser, FaSpinner } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import './MessageDisplay.css';

const MessageDisplay = ({ messages, isLoading }) => {
    const { user } = useAuth();
    // Auto-scroll to bottom when new messages arrive
    const messagesEndRef = React.useRef(null);

    React.useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isLoading]);

    // Get user initial for avatar (same as ProfileSection)
    const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : <FaUser />;

    // Always render container for consistent layout
    return (
        <div className="messages-container">
            {messages && messages.length > 0 && messages.map((message, index) => (
                <div key={index} className={`message-wrapper ${message.type}`}>
                    <div className="message-avatar">
                        {message.type === 'user' ? (
                            <span className="avatar-initial">{userInitial}</span>
                        ) : (
                            <img src="/logo-dark.png" alt="Shreshthaa Logo" className="avatar-logo" />
                        )}
                    </div>
                    <div className="message-content">
                        {message.type === 'user' ? (
                            <div className="user-message">
                                {message.text}
                            </div>
                        ) : (
                            <div className="bot-message">
                                <div className="bot-answer">{message.answer}</div>
                                {message.results && message.results.length > 0 && (
                                    <div className="bot-results">
                                        <div className="results-header">Query Results:</div>
                                        <div className="results-table">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        {Object.keys(message.results[0]).map((key) => (
                                                            <th key={key}>{key}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {message.results.map((row, idx) => (
                                                        <tr key={idx}>
                                                            {Object.values(row).map((value, valIdx) => (
                                                                <td key={valIdx}>
                                                                    {value !== null && value !== undefined 
                                                                        ? String(value) 
                                                                        : '-'}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="message-time">
                            {new Date(message.timestamp).toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                            })}
                        </div>
                    </div>
                </div>
            ))}
            {isLoading && (
                <div className="message-wrapper bot">
                    <div className="message-avatar">
                        <img src="/logo-dark.png" alt="Shreshthaa Logo" className="avatar-logo" />
                    </div>
                    <div className="message-content">
                        <div className="bot-message">
                            <div className="loading-message">
                                <FaSpinner className="spinner-icon" />
                                Processing your query...
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>
    );
};

export default MessageDisplay;

