import React, { useState, useRef } from 'react';
import { FaPlus, FaMicrophone } from 'react-icons/fa';
import { IoMdPulse } from 'react-icons/io';
import useClickOutside from '../../hooks/useClickOutside';
import '../../styles/variables.css';
import './ChatInput.css';

const ChatInput = ({ onMessageSent }) => {
    const [input, setInput] = useState('');
    const [showUploadMenu, setShowUploadMenu] = useState(false);
    const [showModeMenu, setShowModeMenu] = useState(false);
    const [selectedMode, setSelectedMode] = useState('Text Mode');
    const fileInputRef = useRef(null);

    const uploadMenuRef = useRef(null);
    const modeMenuRef = useRef(null);

    useClickOutside(uploadMenuRef, () => setShowUploadMenu(false));
    useClickOutside(modeMenuRef, () => setShowModeMenu(false));

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            console.log('File uploaded:', file.name);
            // Handle file processing here
        }
        setShowUploadMenu(false);
    };

    const triggerFileUpload = () => {
        fileInputRef.current.click();
    };

    const handleMicClick = async () => {
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('Microphone permission granted');
            // Start recording logic here
        } catch (err) {
            console.error('Microphone permission denied', err);
            alert('Microphone permission is required to use voice features.');
        }
    };

    const handleModeSelect = (mode) => {
        setSelectedMode(mode);
        setShowModeMenu(false);
        console.log('Mode selected:', mode);
    };

    const handleSend = () => {
        if (input.trim()) {
            console.log('Message sent:', input);
            // Handle message sending logic here
            if (onMessageSent) {
                onMessageSent();
            }
            setInput(''); // Clear input after sending
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-input-container">
            <div className="relative-container" ref={uploadMenuRef}>
                <button className="add-btn" onClick={() => setShowUploadMenu(!showUploadMenu)}>
                    <FaPlus />
                </button>
                {showUploadMenu && (
                    <div className="dropdown-menu upload-menu">
                        <button onClick={triggerFileUpload}>Upload Excel/CSV</button>
                    </div>
                )}
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept=".csv, .xlsx, .xls"
                    onChange={handleFileUpload}
                />
            </div>

            <input
                type="text"
                placeholder={`Ask anything (${selectedMode})`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                className="chat-input"
            />

            <div className="input-actions">
                <button className="action-btn" onClick={handleMicClick}>
                    <FaMicrophone />
                </button>

                <div className="relative-container" ref={modeMenuRef}>
                    <button className="action-btn" onClick={() => setShowModeMenu(!showModeMenu)}>
                        <IoMdPulse />
                    </button>
                    {showModeMenu && (
                        <div className="dropdown-menu mode-menu">
                            <button onClick={() => handleModeSelect('Text Mode')}>Text Mode</button>
                            <button onClick={() => handleModeSelect('Graph Mode')}>Graph Mode</button>
                            <button onClick={() => handleModeSelect('Table Mode')}>Table Mode</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatInput;
