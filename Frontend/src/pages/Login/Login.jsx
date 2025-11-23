import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import SignUpModal from '../../components/features/SignUpModal';
import './Login.css';

const Login = () => {
    const [activeTab, setActiveTab] = useState('email'); // 'email' or 'mpin'
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [mpin, setMpin] = useState('');
    const [otpSent, setOtpSent] = useState(false);
    const [showSignUp, setShowSignUp] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSendOtp = () => {
        if (email) {
            console.log(`Sending OTP to ${email}`);
            alert(`OTP sent to ${email}. Use 123456 for testing.`);
            setOtpSent(true);
        } else {
            alert('Please enter a valid email.');
        }
    };

    const handleLogin = () => {
        if (activeTab === 'email') {
            if (otp === '123456') {
                login('email', { email });
                navigate('/');
            } else {
                alert('Invalid OTP. Please try again.');
            }
        } else {
            if (mpin === '123456') {
                login('mpin', { mpin });
                navigate('/');
            } else {
                alert('Invalid MPIN. Please try again.');
            }
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h2 className="login-title">Welcome Back</h2>
                <p className="login-subtitle">Please login to your account</p>

                <div className="login-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'email' ? 'active' : ''}`}
                        onClick={() => setActiveTab('email')}
                    >
                        Email & OTP
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'mpin' ? 'active' : ''}`}
                        onClick={() => setActiveTab('mpin')}
                    >
                        MPIN
                    </button>
                </div>

                <div className="login-form">
                    {activeTab === 'email' ? (
                        <>
                            <div className="form-group">
                                <label>Email Address</label>
                                <input
                                    type="email"
                                    className="form-input"
                                    placeholder="Enter your email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label>OTP</label>
                                <div className="otp-group">
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Enter OTP"
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value)}
                                        disabled={!otpSent}
                                    />
                                    <button
                                        className="send-otp-btn"
                                        onClick={handleSendOtp}
                                        disabled={otpSent}
                                    >
                                        {otpSent ? 'Sent' : 'Send OTP'}
                                    </button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="form-group">
                            <label>Enter MPIN</label>
                            <input
                                type="password"
                                className="form-input"
                                placeholder="Enter 6-digit MPIN"
                                maxLength="6"
                                value={mpin}
                                onChange={(e) => setMpin(e.target.value)}
                            />
                        </div>
                    )}

                    <button className="login-btn" onClick={handleLogin}>
                        Login
                    </button>
                </div>

                <div className="signup-link">
                    Don't have an account?
                    <button className="create-account-btn" onClick={() => setShowSignUp(true)}>
                        Create Now
                    </button>
                </div>
            </div>

            {showSignUp && <SignUpModal onClose={() => setShowSignUp(false)} />}
        </div>
    );
};

export default Login;
