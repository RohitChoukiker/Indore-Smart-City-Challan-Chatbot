import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './SignUpModal.css';

const SignUpModal = ({ onClose }) => {
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // 1: Email, 2: OTP
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const { login, requestOTP } = useAuth();
    const navigate = useNavigate();

    const handleSendOtp = async () => {
        if (!email) {
            setError('Please enter a valid email.');
            return;
        }

        setLoading(true);
        setError('');

        const result = await requestOTP(email);

        setLoading(false);

        if (result.success) {
            setStep(2);
            alert(result.message || 'OTP sent successfully!');
        } else {
            setError(result.message || 'Failed to send OTP.');
        }
    };

    const handleVerifyAndSignup = async () => {
        if (!otp) {
            setError('Please enter the OTP.');
            return;
        }

        setLoading(true);
        setError('');

        const result = await login(email, otp);

        setLoading(false);

        if (result.success) {
            onClose();
            navigate('/');
        } else {
            setError(result.message || 'Invalid OTP. Please try again.');
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2 className="modal-title">Create Account</h2>
                <p className="modal-subtitle">Sign up to get started</p>

                {error && <div className="error-message">{error}</div>}

                <div className="form-group">
                    <label>Email Address</label>
                    <input
                        type="email"
                        className="form-input"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={step === 2 || loading}
                    />
                </div>

                {step === 2 && (
                    <div className="form-group">
                        <label>Enter OTP</label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Enter 6-digit OTP"
                            value={otp}
                            onChange={(e) => setOtp(e.target.value)}
                            disabled={loading}
                        />
                    </div>
                )}

                <div className="modal-actions">
                    {step === 1 ? (
                        <button
                            className="primary-btn"
                            onClick={handleSendOtp}
                            disabled={loading}
                        >
                            {loading ? 'Sending...' : 'Verify Email'}
                        </button>
                    ) : (
                        <button
                            className="primary-btn"
                            onClick={handleVerifyAndSignup}
                            disabled={loading}
                        >
                            {loading ? 'Creating...' : 'Create Account'}
                        </button>
                    )}
                    <button
                        className="secondary-btn"
                        onClick={onClose}
                        disabled={loading}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SignUpModal;
