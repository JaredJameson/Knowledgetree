/**
 * KnowledgeTree - Sidebar Navigation Component
 * Provides navigation to all main sections
 */

import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useSignOut } from '@/hooks/use-sign-out';
import {
  Home,
  FolderKanban,
  FileText,
  MessageSquare,
  Search,
  Brain,
  Workflow,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { LanguageSwitcher } from './language-switcher';
import { ThemeToggle } from './theme-toggle';
import { useTheme } from './theme-provider';

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuth();
  const signOut = useSignOut();
  const { theme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Projekty', href: '/projects', icon: FolderKanban },
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Dokumenty', href: '/documents', icon: FileText },
    { name: 'Wyszukiwanie', href: '/search', icon: Search },
    { name: 'AI Insights', href: '/insights', icon: Brain },
    { name: 'Workflows', href: '/workflows', icon: Workflow },
    { name: 'Ustawienia', href: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    signOut();
  };

  return (
    <div
      className={cn(
        "flex flex-col bg-white dark:bg-neutral-950 border-r border-neutral-200 dark:border-neutral-800 transition-all duration-300",
        collapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-neutral-200 dark:border-neutral-800">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <img
              src={theme === 'dark' ? '/logo_biale.png' : '/logo_czarne.png'}
              alt="KnowledgeTree Logo"
              className="h-10 w-auto object-contain"
            />
            <span className="font-semibold text-lg text-neutral-900 dark:text-neutral-50">
              KnowledgeTree
            </span>
          </div>
        )}
        {collapsed && (
          <div className="flex items-center justify-center w-full">
            <img
              src={theme === 'dark' ? '/logo_biale.png' : '/logo_czarne.png'}
              alt="KnowledgeTree Logo"
              className="h-8 w-auto object-contain"
            />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5 text-neutral-600 dark:text-neutral-400" />
          ) : (
            <ChevronLeft className="h-5 w-5 text-neutral-600 dark:text-neutral-400" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href ||
                          (item.href !== '/dashboard' && location.pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-400"
                  : "text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800",
                collapsed && "justify-center"
              )}
              title={collapsed ? item.name : undefined}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="border-t border-neutral-200 dark:border-neutral-800 p-4">
        {!collapsed && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
              <span className="text-neutral-700 dark:text-neutral-300 truncate">
                {user?.email}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <LanguageSwitcher />
              <ThemeToggle />
              <button
                onClick={handleLogout}
                className="p-2 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                title="Wyloguj"
              >
                <LogOut className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
              </button>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="flex flex-col gap-2">
            <button
              onClick={handleLogout}
              className="p-2 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors mx-auto"
              title="Wyloguj"
            >
              <LogOut className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
