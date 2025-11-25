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
            setOtpSent(true);
            alert(result.message || 'OTP sent successfully!');
        } else {
            setError(result.message || 'Failed to send OTP.');
        }
    };

    const handleLogin = async () => {
        if (activeTab === 'email') {
            if (!otp) {
                setError('Please enter the OTP.');
                return;
            }

            setLoading(true);
            setError('');

            const result = await login(email, otp);

            setLoading(false);

            if (result.success) {
                navigate('/');
            } else {
                setError(result.message || 'Invalid OTP. Please try again.');
            }
        } else {
            // MPIN login - not yet implemented in backend
            setError('MPIN login is not yet available. Please use Email & OTP.');
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

                {error && <div className="error-message">{error}</div>}

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
                                    disabled={loading}
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
                                        disabled={!otpSent || loading}
                                    />
                                    <button
                                        className="send-otp-btn"
                                        onClick={handleSendOtp}
                                        disabled={otpSent || loading}
                                    >
                                        {loading ? 'Sending...' : otpSent ? 'Sent' : 'Send OTP'}
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
                                disabled={loading}
                            />
                        </div>
                    )}

                    <button
                        className="login-btn"
                        onClick={handleLogin}
                        disabled={loading}
                    >
                        {loading ? 'Logging in...' : 'Login'}
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
