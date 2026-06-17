'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export function useRequireAdmin(): boolean {
  const router = useRouter();
  const { isLoggedIn, user } = useAuth();

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace('/login');
    } else if (user?.role !== 'admin') {
      router.replace('/');
    }
  }, [isLoggedIn, user, router]);

  return isLoggedIn && user?.role === 'admin';
}
