import React from 'react';
import { Outlet } from 'react-router-dom';
import ProfileSection from '../features/ProfileSection';

const MainLayout = () => {
    return (
        <div className="main-layout">
            <main className="content-area">
                <Outlet />
            </main>
            <ProfileSection />
        </div>
    );
};

export default MainLayout;
