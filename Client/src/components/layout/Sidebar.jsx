import React from 'react';
import { FaPlus, FaQuestionCircle, FaCog, FaHistory } from 'react-icons/fa';
import '../../styles/variables.css';

const Sidebar = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <button className="menu-icon">
            <span className="material-symbols-outlined">menu</span>
        </button>
        <button className="new-chat-btn">
          <FaPlus />
          <span>New chat</span>
        </button>
      </div>
      
      <div className="sidebar-middle">
        <div className="recent-chats">
            <p className="recent-title">Recent</p>
            {/* Recent items will go here */}
        </div>
      </div>

      <div className="sidebar-bottom">
        <button className="sidebar-item">
            <FaQuestionCircle />
            <span>Help</span>
        </button>
        <button className="sidebar-item">
            <FaHistory />
            <span>Activity</span>
        </button>
        <button className="sidebar-item">
            <FaCog />
            <span>Settings</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
