import React, { useState } from 'react';
import { FaUser, FaMoon, FaSun, FaSignOutAlt, FaUserCircle } from 'react-icons/fa';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import ProfileModal from './ProfileModal';

import './ProfileSection.css';

const ProfileSection = () => {
    const [showMenu, setShowMenu] = useState(false);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const { theme, toggleTheme } = useTheme();
    const { logout, user } = useAuth();

    const handleGetProfile = () => {
        setShowMenu(false);
        setShowProfileModal(true);
    };

    const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : <FaUser />;

    return (
        <>
            <div className="profile-section">
                {showMenu && (
                    <div className="profile-menu">
                        <button onClick={handleGetProfile}>
                            <FaUserCircle /> Get Profile
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
        </>
    );
};

export default ProfileSection;
