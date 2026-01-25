/**
 * KnowledgeTree - Sign Out Hook
 * Hook for signing out user
 */

import { useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';

export function useSignOut() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const signOut = useCallback(() => {
    logout();
    navigate('/login', { replace: true });
  }, [logout, navigate]);

  return signOut;
}
