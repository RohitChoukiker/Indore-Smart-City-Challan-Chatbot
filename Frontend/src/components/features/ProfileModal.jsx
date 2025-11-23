import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { FaTimes, FaEdit, FaSave } from 'react-icons/fa';
import './ProfileModal.css';

const ProfileModal = ({ onClose }) => {
    const { user, updateProfile } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        department: '',
        designation: ''
    });

    useEffect(() => {
        if (user) {
            setFormData({
                name: user.name || '',
                department: user.department || '',
                designation: user.designation || ''
            });
        }
    }, [user]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = () => {
        updateProfile(formData);
        setIsEditing(false);
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content profile-modal-content">
                <div className="modal-header">
                    <h2 className="modal-title">User Profile</h2>
                    <button className="close-btn" onClick={onClose}>
                        <FaTimes />
                    </button>
                </div>

                <div className="profile-form">
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
                            <button className="primary-btn save-btn" onClick={handleSave}>
                                <FaSave /> Save Changes
                            </button>
                            <button className="secondary-btn" onClick={() => setIsEditing(false)}>
                                Cancel
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProfileModal;
