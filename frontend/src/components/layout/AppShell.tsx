import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppShell: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Desktop Sidebar */}
      <div className="hidden shrink-0 md:flex">
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />
      </div>

      {/* Mobile Sidebar Overlay / Drawer */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-950/45 backdrop-blur-[2px] transition-opacity"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 flex h-full w-[17rem] max-w-[86vw] flex-col bg-card shadow-2xl">
            <Sidebar
              isCollapsed={false}
              onToggleCollapse={() => setIsMobileMenuOpen(false)}
              onNavigateMobile={() => setIsMobileMenuOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex min-w-0 flex-1 flex-col overflow-x-hidden">
        <TopBar onOpenMobileMenu={() => setIsMobileMenuOpen(true)} />
        <main className="w-full flex-1">
          <div className="mx-auto w-full max-w-[1320px] px-4 py-5 sm:px-6 sm:py-7 lg:px-8 lg:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
