import React, { useState, useRef, useEffect } from 'react';
import { FaPlus, FaMicrophone, FaPaperPlane, FaCheckCircle, FaFileExcel, FaTrash, FaCheck } from 'react-icons/fa';
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
    const [selectedFileId, setSelectedFileId] = useState(null);
    const [loadingFiles, setLoadingFiles] = useState(false);
    const [deletingFileId, setDeletingFileId] = useState(null);
    const fileInputRef = useRef(null);

    const uploadMenuRef = useRef(null);
    const modeMenuRef = useRef(null);

    useClickOutside(uploadMenuRef, () => setShowUploadMenu(false));
    useClickOutside(modeMenuRef, () => setShowModeMenu(false));

    // Fetch files from API on mount
    useEffect(() => {
        fetchFiles();
    }, []);

    // Fetch files from API
    const fetchFiles = async () => {
        setLoadingFiles(true);
        try {
            const response = await agentAPI.listFiles();
            if (response.status && response.data) {
                const files = response.data.files || [];
                setUploadedFiles(files);
                // Auto-select the first file (most recent) if none selected
                if (files.length > 0 && !selectedFileId) {
                    setSelectedFileId(files[0].id);
                }
            }
        } catch (error) {
            console.error('Error fetching files:', error);
        } finally {
            setLoadingFiles(false);
        }
    };

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
                // Refresh files list from API
                await fetchFiles();
                
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
            
            // Get selected file's table_name
            const selectedFile = uploadedFiles.find(f => f.id === selectedFileId);
            const tableName = selectedFile ? selectedFile.table_name : null;
            
            // Set loading state
            if (onQueryLoading) {
                onQueryLoading(true);
            }
            
            // Clear input immediately for better UX
            setInput('');
            
            try {
                // Call query API with mode and table_name
                const response = await agentAPI.query(queryText, 5, mode, tableName);
                
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

    const handleFileSelect = (fileId) => {
        setSelectedFileId(fileId);
        setShowUploadMenu(false);
    };

    const handleFileDelete = async (fileId, e) => {
        e.stopPropagation(); // Prevent file selection when clicking delete
        
        if (!window.confirm('Are you sure you want to delete this file? This will also delete all its data from the database.')) {
            return;
        }

        setDeletingFileId(fileId);
        try {
            const response = await agentAPI.deleteFile(fileId);
            if (response.status) {
                // Refresh files list
                await fetchFiles();
                // Clear selection if deleted file was selected
                if (selectedFileId === fileId) {
                    setSelectedFileId(null);
                }
            } else {
                alert(response.message || 'Failed to delete file');
            }
        } catch (error) {
            console.error('Error deleting file:', error);
            alert(error.message || 'Failed to delete file. Please try again.');
        } finally {
            setDeletingFileId(null);
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
                        <button onClick={triggerFileUpload} className="upload-btn">
                            <FaFileExcel /> Upload Excel/CSV
                        </button>
                        {loadingFiles ? (
                            <div className="loading-files">
                                <span className="loading-spinner"></span>
                                Loading files...
                            </div>
                        ) : uploadedFiles.length > 0 ? (
                            <div className="uploaded-files-section">
                                <div className="uploaded-files-header">
                                    Uploaded Files ({uploadedFiles.length})
                                    {selectedFileId && (
                                        <span className="selected-indicator">• Active</span>
                                    )}
                                </div>
                                <div className="uploaded-files-list">
                                    {uploadedFiles.map((file) => {
                                        const isSelected = file.id === selectedFileId;
                                        const isDeleting = deletingFileId === file.id;
                                        return (
                                            <div 
                                                key={file.id} 
                                                className={`uploaded-file-item ${isSelected ? 'selected' : ''}`}
                                                onClick={() => handleFileSelect(file.id)}
                                            >
                                                <FaFileExcel className="file-icon" />
                                                <div className="file-info">
                                                    <div className="file-name">
                                                        {file.filename || file.name || 'Untitled File'}
                                                        {isSelected && (
                                                            <FaCheck className="selected-check-icon" />
                                                        )}
                                                    </div>
                                                    <div className="file-meta">
                                                        {file.row_count || file.rowsStored || 0} rows • {formatDate(file.created_at || file.uploadedAt || new Date().toISOString())}
                                                    </div>
                                                </div>
                                                <div className="file-actions">
                                                    {isSelected && (
                                                        <span className="active-badge">Active</span>
                                                    )}
                                                    <button
                                                        className="delete-file-btn"
                                                        onClick={(e) => handleFileDelete(file.id, e)}
                                                        disabled={isDeleting}
                                                        title="Delete file"
                                                    >
                                                        {isDeleting ? (
                                                            <span className="loading-spinner small"></span>
                                                        ) : (
                                                            <FaTrash />
                                                        )}
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div className="no-files-message">
                                No files uploaded yet. Upload a file to get started.
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
