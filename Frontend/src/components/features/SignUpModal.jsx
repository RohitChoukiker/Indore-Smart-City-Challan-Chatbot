import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './SignUpModal.css';

const SignUpModal = ({ onClose }) => {
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // 1: Email, 2: OTP
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSendOtp = () => {
        if (email) {
            console.log(`Sending OTP to ${email}`);
            alert(`OTP sent to ${email}. Use 123456 for testing.`);
            setStep(2);
        } else {
            alert('Please enter a valid email.');
        }
    };

    const handleVerifyAndSignup = () => {
        if (otp === '123456') {
            login('signup', { email });
            onClose();
            navigate('/');
        } else {
            alert('Invalid OTP. Please try again.');
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2 className="modal-title">Create Account</h2>
                <p className="modal-subtitle">Sign up to get started</p>

                <div className="form-group">
                    <label>Email Address</label>
                    <input
                        type="email"
                        className="form-input"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={step === 2}
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
                        />
                    </div>
                )}

                <div className="modal-actions">
                    {step === 1 ? (
                        <button className="primary-btn" onClick={handleSendOtp}>Verify Email</button>
                    ) : (
                        <button className="primary-btn" onClick={handleVerifyAndSignup}>Create Account</button>
                    )}
                    <button className="secondary-btn" onClick={onClose}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default SignUpModal;
