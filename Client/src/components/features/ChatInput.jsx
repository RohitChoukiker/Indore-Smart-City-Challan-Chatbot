import React, { useState, useRef, useEffect } from 'react';
import { FaPlus, FaMicrophone, FaPaperPlane, FaCheckCircle, FaFileExcel, FaTrash, FaCheck } from 'react-icons/fa';
import { agentAPI } from '../../services/api';
import useClickOutside from '../../hooks/useClickOutside';
import '../../styles/variables.css';
import './ChatInput.css';

const ChatInput = ({ onMessageSent, onQueryLoading, selectedMode, triggerUpload, onUploadTriggered }) => {
    const [input, setInput] = useState('');
    const [showUploadMenu, setShowUploadMenu] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [uploadingFile, setUploadingFile] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [selectedFileId, setSelectedFileId] = useState(null);
    const [loadingFiles, setLoadingFiles] = useState(false);
    const [deletingFileId, setDeletingFileId] = useState(null);
    const fileInputRef = useRef(null);
    const uploadMenuRef = useRef(null);

    useClickOutside(uploadMenuRef, () => setShowUploadMenu(false));

    useEffect(() => {
        fetchFiles();
    }, []);

    // When Home triggers upload via top bar button
    useEffect(() => {
        if (triggerUpload) {
            triggerFileUpload({ preventDefault: () => {}, stopPropagation: () => {} });
            if (onUploadTriggered) onUploadTriggered();
        }
    }, [triggerUpload]);

    const fetchFiles = async () => {
        setLoadingFiles(true);
        try {
            const response = await agentAPI.listFiles();
            if (response.status && response.data) {
                const files = response.data.files || [];
                setUploadedFiles(files);
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
        const file = e.target?.files?.[0];
        if (!file) {
            setShowUploadMenu(false);
            return;
        }

        const validTypes = ['.xlsx', '.xls', '.csv'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!validTypes.includes(fileExtension)) {
            alert('Please upload a valid Excel file (.xlsx, .xls, or .csv)');
            setShowUploadMenu(false);
            return;
        }

        setUploadingFile({ name: file.name, size: file.size, id: Date.now() });
        setUploadProgress(0);
        setShowUploadMenu(false);

        let progressInterval;
        try {
            progressInterval = setInterval(() => {
                setUploadProgress((prev) => {
                    if (prev >= 90) { clearInterval(progressInterval); return 90; }
                    return prev + 10;
                });
            }, 200);

            const response = await agentAPI.uploadExcel(file);
            clearInterval(progressInterval);
            setUploadProgress(100);

            if (response && response.status) {
                await fetchFiles();
                setTimeout(() => { setUploadingFile(null); setUploadProgress(0); }, 2000);
            } else {
                throw new Error(response.message || 'Upload failed');
            }
        } catch (error) {
            if (progressInterval) clearInterval(progressInterval);
            const errorMessage = error.response?.message || error.message || 'Upload failed. Please try again.';
            setUploadingFile((prev) => ({ ...prev, status: 'error', error: errorMessage }));
            setUploadProgress(0);
            setTimeout(() => setUploadingFile(null), 3000);
        }

        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const triggerFileUpload = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setShowUploadMenu(false);
        setTimeout(() => { if (fileInputRef.current) fileInputRef.current.click(); }, 50);
    };

    const handleMicClick = async () => {
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (err) {
            alert('Microphone permission is required to use voice features.');
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;
        const queryText = input.trim();
        const mode = selectedMode || 'text';
        const selectedFile = uploadedFiles.find(f => f.id === selectedFileId);
        const tableName = selectedFile ? selectedFile.table_name : null;

        if (onQueryLoading) onQueryLoading(true);
        setInput('');

        try {
            const response = await agentAPI.query(queryText, 5, mode, tableName);
            if (onMessageSent) {
                onMessageSent(queryText, response.status ? response : {
                    status: false,
                    message: response.message || 'Query failed',
                    data: null,
                });
            }
        } catch (error) {
            if (onMessageSent) {
                onMessageSent(queryText, {
                    status: false,
                    message: error.message || 'Failed to process query. Please try again.',
                    data: null,
                });
            }
        } finally {
            if (onQueryLoading) onQueryLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
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
        e.stopPropagation();
        if (!window.confirm('Are you sure you want to delete this file? This will also delete all its data from the database.')) return;
        setDeletingFileId(fileId);
        try {
            const response = await agentAPI.deleteFile(fileId);
            if (response.status) {
                await fetchFiles();
                if (selectedFileId === fileId) setSelectedFileId(null);
            } else {
                alert(response.message || 'Failed to delete file');
            }
        } catch (error) {
            alert(error.message || 'Failed to delete file. Please try again.');
        } finally {
            setDeletingFileId(null);
        }
    };

    return (
        <div className="chat-input-container">
            {/* Plus / Upload menu */}
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
                                    {selectedFileId && <span className="selected-indicator">• Active</span>}
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
                                                        {isSelected && <FaCheck className="selected-check-icon" />}
                                                    </div>
                                                    <div className="file-meta">
                                                        {file.row_count || file.rowsStored || 0} rows • {formatDate(file.created_at || file.uploadedAt || new Date().toISOString())}
                                                    </div>
                                                </div>
                                                <div className="file-actions">
                                                    {isSelected && <span className="active-badge">Active</span>}
                                                    <button
                                                        className="delete-file-btn"
                                                        onClick={(e) => handleFileDelete(file.id, e)}
                                                        disabled={isDeleting}
                                                        title="Delete file"
                                                    >
                                                        {isDeleting ? <span className="loading-spinner small"></span> : <FaTrash />}
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div className="no-files-message">No files uploaded yet. Upload a file to get started.</div>
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

            {/* Text input */}
            <div className="input-wrapper">
                <input
                    type="text"
                    placeholder={`Ask about challans, zones, trends...`}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="chat-input"
                />
            </div>

            {/* Mic + Send */}
            <div className="input-actions">
                <button className="action-btn" onClick={handleMicClick} title="Voice input">
                    <FaMicrophone />
                </button>
                <button
                    className={`send-btn ${input.trim() ? 'visible' : ''}`}
                    onClick={handleSend}
                    title="Send query"
                    disabled={!input.trim()}
                >
                    <FaPaperPlane />
                </button>
            </div>

            {/* Upload progress overlay */}
            {uploadingFile && (
                <div className="upload-progress-overlay">
                    <div className={`upload-progress-card ${uploadingFile.status === 'error' ? 'error' : uploadProgress === 100 ? 'success' : ''}`}>
                        <div className="upload-progress-header">
                            <FaFileExcel className="upload-icon" />
                            <span className="upload-file-name">{uploadingFile.name}</span>
                        </div>
                        {uploadingFile.status === 'error' ? (
                            <div className="upload-error"><p>{uploadingFile.error}</p></div>
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
                                        <><span className="loading-spinner"></span> Uploading... {uploadProgress}%</>
                                    ) : (
                                        <><FaCheckCircle className="success-check-icon" /> Upload successful!</>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatInput;