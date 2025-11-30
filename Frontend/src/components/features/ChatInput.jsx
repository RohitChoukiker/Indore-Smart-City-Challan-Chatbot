import React, { useState, useRef, useEffect } from 'react';
import { FaPlus, FaMicrophone, FaPaperPlane, FaCheckCircle, FaFileExcel } from 'react-icons/fa';
import { IoMdPulse } from 'react-icons/io';
import { agentAPI } from '../../services/api';
import useClickOutside from '../../hooks/useClickOutside';
import '../../styles/variables.css';
import './ChatInput.css';

const ChatInput = ({ onMessageSent, onQueryLoading }) => {
    const [input, setInput] = useState('');
    const [showUploadMenu, setShowUploadMenu] = useState(false);
    const [showModeMenu, setShowModeMenu] = useState(false);
    const [selectedMode, setSelectedMode] = useState('Text Mode');
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [uploadingFile, setUploadingFile] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const fileInputRef = useRef(null);

    const uploadMenuRef = useRef(null);
    const modeMenuRef = useRef(null);

    useClickOutside(uploadMenuRef, () => setShowUploadMenu(false));
    useClickOutside(modeMenuRef, () => setShowModeMenu(false));

    // Load uploaded files from localStorage on mount
    useEffect(() => {
        const savedFiles = localStorage.getItem('uploadedFiles');
        if (savedFiles) {
            try {
                setUploadedFiles(JSON.parse(savedFiles));
            } catch (e) {
                console.error('Error loading uploaded files:', e);
            }
        }
    }, []);

    // Save uploaded files to localStorage whenever it changes
    useEffect(() => {
        if (uploadedFiles.length > 0) {
            localStorage.setItem('uploadedFiles', JSON.stringify(uploadedFiles));
        }
    }, [uploadedFiles]);

    const handleFileUpload = async (e) => {
        console.log('File input changed:', e.target.files);
        const file = e.target?.files?.[0];
        if (!file) {
            console.log('No file selected or file selection cancelled');
            setShowUploadMenu(false);
            return;
        }
        
        console.log('File selected:', {
            name: file.name,
            size: file.size,
            type: file.type
        });

        // Validate file type
        const validTypes = ['.xlsx', '.xls', '.csv'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!validTypes.includes(fileExtension)) {
            alert('Please upload a valid Excel file (.xlsx, .xls, or .csv)');
            setShowUploadMenu(false);
            return;
        }

        // Set uploading state
        console.log('Starting upload process for:', file.name);
        setUploadingFile({
            name: file.name,
            size: file.size,
            id: Date.now(),
        });
        setUploadProgress(0);
        setShowUploadMenu(false);

        let progressInterval;
        try {
            console.log('Calling uploadExcel API...');
            // Simulate progress (since axios doesn't provide upload progress easily)
            progressInterval = setInterval(() => {
                setUploadProgress((prev) => {
                    if (prev >= 90) {
                        if (progressInterval) clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            // Upload file
            const response = await agentAPI.uploadExcel(file);
            console.log('Upload response:', response);
            
            if (progressInterval) {
                clearInterval(progressInterval);
            }
            setUploadProgress(100);

            if (response && response.status) {
                // Add to uploaded files list
                const newFile = {
                    id: Date.now(),
                    name: file.name,
                    tableName: response.data.table_name,
                    rowsStored: response.data.rows_stored,
                    uploadedAt: new Date().toISOString(),
                    status: 'success',
                };

                setUploadedFiles((prev) => [newFile, ...prev]);

                // Show success message briefly
                setTimeout(() => {
                    setUploadingFile(null);
                    setUploadProgress(0);
                }, 2000);
            } else {
                throw new Error(response.message || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            console.error('Error details:', {
                message: error.message,
                response: error.response,
                status: error.response?.status,
                data: error.response?.data
            });
            if (progressInterval) {
                clearInterval(progressInterval);
            }
            const errorMessage = error.response?.message || error.message || 'Upload failed. Please try again.';
            console.error('Error message:', errorMessage);
            setUploadingFile((prev) => ({
                ...prev,
                status: 'error',
                error: errorMessage,
            }));
            setUploadProgress(0);
            
            setTimeout(() => {
                setUploadingFile(null);
            }, 3000);
        }

        // Reset file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const triggerFileUpload = (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Triggering file upload, fileInputRef:', fileInputRef.current);
        if (fileInputRef.current) {
            // Close menu first
            setShowUploadMenu(false);
            // Trigger file input click after a small delay to ensure menu closes
            setTimeout(() => {
                if (fileInputRef.current) {
                    fileInputRef.current.click();
                }
            }, 50);
        } else {
            console.error('File input ref is null');
            alert('File upload not available. Please refresh the page.');
        }
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

    const handleSend = async () => {
        if (input.trim()) {
            const queryText = input.trim();
            console.log('Message sent:', queryText);
            
            // Extract mode from selectedMode (e.g., "Text Mode" -> "text")
            const mode = selectedMode.toLowerCase().replace(' mode', '');
            
            // Set loading state
            if (onQueryLoading) {
                onQueryLoading(true);
            }
            
            // Clear input immediately for better UX
            setInput('');
            
            try {
                // Call query API with mode
                const response = await agentAPI.query(queryText, 5, mode);
                
                // Handle response
                if (response.status) {
                    // Success - pass query and response to parent
                    if (onMessageSent) {
                        onMessageSent(queryText, response);
                    }
                } else {
                    // API returned error
                    const errorResponse = {
                        status: false,
                        message: response.message || 'Query failed',
                        data: null
                    };
                    if (onMessageSent) {
                        onMessageSent(queryText, errorResponse);
                    }
                }
            } catch (error) {
                console.error('Query error:', error);
                // Handle error response
                const errorResponse = {
                    status: false,
                    message: error.message || error.response?.message || 'Failed to process query. Please try again.',
                    data: null
                };
                if (onMessageSent) {
                    onMessageSent(queryText, errorResponse);
                }
            } finally {
                // Clear loading state
                if (onQueryLoading) {
                    onQueryLoading(false);
                }
            }
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="chat-input-container">
            <div className="relative-container" ref={uploadMenuRef}>
                <button className="add-btn" onClick={() => setShowUploadMenu(!showUploadMenu)}>
                    <FaPlus />
                </button>
                {showUploadMenu && (
                    <div className="dropdown-menu upload-menu">
                        <button onClick={triggerFileUpload} className="upload-btn">
                            <FaFileExcel /> Upload Excel/CSV
                        </button>
                        {uploadedFiles.length > 0 && (
                            <div className="uploaded-files-section">
                                <div className="uploaded-files-header">Uploaded Files ({uploadedFiles.length})</div>
                                <div className="uploaded-files-list">
                                    {uploadedFiles.map((file) => (
                                        <div key={file.id} className="uploaded-file-item">
                                            <FaFileExcel className="file-icon" />
                                            <div className="file-info">
                                                <div className="file-name">{file.name}</div>
                                                <div className="file-meta">
                                                    {file.rowsStored} rows • {formatDate(file.uploadedAt)}
                                                </div>
                                            </div>
                                            {file.status === 'success' && (
                                                <div className="success-icon-wrapper">
                                                    <FaCheckCircle className="success-icon" />
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept=".csv,.xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
                    onChange={handleFileUpload}
                    id="excel-file-input"
                />
            </div>

            <div className="input-wrapper">
                <input
                    type="text"
                    placeholder={`Ask anything (${selectedMode})`}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="chat-input"
                />
                {input.trim() && (
                    <button className="send-btn visible" onClick={handleSend} title="Send query">
                        <FaPaperPlane />
                    </button>
                )}
            </div>

            {uploadingFile && (
                <div className="upload-progress-overlay">
                    <div className={`upload-progress-card ${uploadingFile.status === 'error' ? 'error' : uploadProgress === 100 ? 'success' : ''}`}>
                        <div className="upload-progress-header">
                            <FaFileExcel className="upload-icon" />
                            <span className="upload-file-name">{uploadingFile.name}</span>
                        </div>
                        {uploadingFile.status === 'error' ? (
                            <div className="upload-error">
                                <p>{uploadingFile.error}</p>
                            </div>
                        ) : (
                            <>
                                <div className="upload-progress-bar">
                                    <div 
                                        className={`upload-progress-fill ${uploadProgress === 100 ? 'success' : 'loading'}`}
                                        style={{ width: `${uploadProgress}%` }}
                                    ></div>
                                </div>
                                <div className="upload-progress-text">
                                    {uploadProgress < 100 ? (
                                        <>
                                            <span className="loading-spinner"></span>
                                            Uploading... {uploadProgress}%
                                        </>
                                    ) : (
                                        <>
                                            <FaCheckCircle className="success-check-icon" />
                                            Upload successful!
                                        </>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

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
