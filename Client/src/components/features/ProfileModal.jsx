import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';
import { FaTimes, FaEdit, FaSave } from 'react-icons/fa';
import './ProfileModal.css';

const ProfileModal = ({ onClose }) => {
    const { user, updateProfile } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [toast, setToast] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        department: '',
        designation: ''
    });

    const showToast = (message) => {
        setToast(message);
        setTimeout(() => setToast(''), 3000);
    };

    // Fetch profile data when modal opens
    useEffect(() => {
        const fetchProfile = async () => {
            try {
                setLoading(true);
                const response = await authAPI.getProfile();

                if (response.status) {
                    setFormData({
                        name: response.data.name || '',
                        email: response.data.email || '',
                        department: response.data.department || '',
                        designation: response.data.designation || ''
                    });
                } else {
                    setError(response.message || 'Failed to load profile');
                }
            } catch (err) {
                setError(err.message || 'Failed to load profile');
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = async () => {
        setSaving(true);
        setError('');

        try {
            // Call the updateProfile from AuthContext which now uses the API
            const result = await updateProfile({
                name: formData.name,
                department: formData.department,
                designation: formData.designation
            });

            if (result.success) {
                setIsEditing(false);
                showToast('Profile updated successfully!');
            } else {
                setError(result.message || 'Failed to update profile');
            }
        } catch (err) {
            setError(err.message || 'Failed to update profile');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="modal-overlay">
            {toast && <div className="toast-notification">{toast}</div>}

            <div className="modal-content profile-modal-content">
                <div className="modal-header">
                    <h2 className="modal-title">User Profile</h2>
                    <button className="close-btn" onClick={onClose}>
                        <FaTimes />
                    </button>
                </div>

                {loading ? (
                    <div className="loading-message">Loading profile...</div>
                ) : (
                    <>
                        {error && <div className="error-message">{error}</div>}

                        <div className="profile-form">
                            <div className="form-group">
                                <label>Email</label>
                                <input
                                    type="email"
                                    className="form-input disabled"
                                    value={formData.email}
                                    disabled
                                />
                            </div>

                            <div className="form-group">
                                <label>Name</label>
                                <input
                                    type="text"
                                    name="name"
                                    className={`form-input ${!isEditing ? 'disabled' : ''}`}
                                    value={formData.name}
                                    onChange={handleChange}
                                    disabled={!isEditing}
                                />
                            </div>

                            <div className="form-group">
                                <label>Department</label>
                                <input
                                    type="text"
                                    name="department"
                                    className={`form-input ${!isEditing ? 'disabled' : ''}`}
                                    value={formData.department}
                                    onChange={handleChange}
                                    disabled={!isEditing}
                                />
                            </div>

                            <div className="form-group">
                                <label>Designation</label>
                                <input
                                    type="text"
                                    name="designation"
                                    className={`form-input ${!isEditing ? 'disabled' : ''}`}
                                    value={formData.designation}
                                    onChange={handleChange}
                                    disabled={!isEditing}
                                />
                            </div>
                        </div>

                        <div className="modal-actions">
                            {!isEditing ? (
                                <button className="primary-btn edit-btn" onClick={() => setIsEditing(true)}>
                                    <FaEdit /> Edit Profile
                                </button>
                            ) : (
                                <>
                                    <button
                                        className="primary-btn save-btn"
                                        onClick={handleSave}
                                        disabled={saving}
                                    >
                                        <FaSave /> {saving ? 'Saving...' : 'Save Changes'}
                                    </button>
                                    <button
                                        className="secondary-btn"
                                        onClick={() => setIsEditing(false)}
                                        disabled={saving}
                                    >
                                        Cancel
                                    </button>
                                </>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default ProfileModal;
