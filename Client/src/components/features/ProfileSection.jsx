import React, { useState, useRef } from 'react';
import { FaUser, FaMoon, FaSun, FaSignOutAlt, FaUserCircle, FaKey } from 'react-icons/fa';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import ProfileModal from './ProfileModal';
import MPINModal from './MPINModal';
import useClickOutside from '../../hooks/useClickOutside';

import './ProfileSection.css';

const ProfileSection = () => {
    const [showMenu, setShowMenu] = useState(false);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [showMPINModal, setShowMPINModal] = useState(false);
    const { theme, toggleTheme } = useTheme();
    const { logout, user } = useAuth();

    const menuRef = useRef(null);
    useClickOutside(menuRef, () => setShowMenu(false));

    const handleGetProfile = () => {
        setShowMenu(false);
        setShowProfileModal(true);
    };

    const handleSetMPIN = () => {
        setShowMenu(false);
        setShowMPINModal(true);
    };

    const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : <FaUser />;

    return (
        <>
            <div className="profile-section" ref={menuRef}>
                {showMenu && (
                    <div className="profile-menu">
                        <button onClick={handleGetProfile}>
                            <FaUserCircle /> Get Profile
                        </button>
                        <button onClick={handleSetMPIN}>
                            <FaKey /> Set MPIN
                        </button>
                        <button onClick={toggleTheme}>
                            {theme === 'dark' ? <FaSun /> : <FaMoon />}
                            {theme === 'dark' ? ' Light Mode' : ' Dark Mode'}
                        </button>
                        <button onClick={logout}>
                            <FaSignOutAlt /> Logout
                        </button>
                    </div>
                )}
                <button
                    className="profile-btn"
                    onClick={() => setShowMenu(!showMenu)}
                    title="User Profile"
                >
                    {userInitial}
                </button>
            </div>
            {showProfileModal && <ProfileModal onClose={() => setShowProfileModal(false)} />}
            {showMPINModal && <MPINModal onClose={() => setShowMPINModal(false)} />}
        </>
    );
};

export default ProfileSection;
