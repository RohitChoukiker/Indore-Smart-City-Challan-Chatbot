import React, { useState } from 'react';
import { authAPI } from '../../services/api';
import { FaTimes, FaKey } from 'react-icons/fa';
import './MPINModal.css';

const MPINModal = ({ onClose }) => {
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    const handleSendMPIN = async () => {
        setLoading(true);
        setError('');

        try {
            const response = await authAPI.setMPIN();

            if (response.status) {
                setSuccess(true);
                setTimeout(() => {
                    onClose();
                }, 3000);
            } else {
                setError(response.message || 'Failed to send MPIN');
            }
        } catch (err) {
            setError(err.message || 'Failed to send MPIN');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content mpin-modal-content">
                <div className="modal-header">
                    <h2 className="modal-title">Set MPIN</h2>
                    <button className="close-btn" onClick={onClose}>
                        <FaTimes />
                    </button>
                </div>

                {success ? (
                    <div className="success-content">
                        <div className="success-icon">✓</div>
                        <p className="success-message">
                            MPIN has been sent to your registered email address!
                        </p>
                        <p className="success-submessage">
                            Please check your inbox.
                        </p>
                    </div>
                ) : (
                    <>
                        {error && <div className="error-message">{error}</div>}

                        <div className="mpin-info">
                            <FaKey className="mpin-icon" />
                            <p className="mpin-description">
                                Click the button below to generate and send a new MPIN to your registered email address.
                            </p>
                        </div>

                        <div className="modal-actions">
                            <button
                                className="primary-btn"
                                onClick={handleSendMPIN}
                                disabled={loading}
                            >
                                {loading ? 'Sending...' : 'Send MPIN to Email'}
                            </button>
                            <button
                                className="secondary-btn"
                                onClick={onClose}
                                disabled={loading}
                            >
                                Cancel
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default MPINModal;
