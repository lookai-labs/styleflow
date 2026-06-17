'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from './ui/button';
import { Menu, X } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export function Header() {
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (user?.role === 'admin') {
    return (
      <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/admin" className="text-2xl tracking-tight font-normal">
              StyleFlow Admin
            </Link>
            <nav className="flex items-center gap-6">
              <span className="text-sm text-gray-500">{user.nickname}님</span>
              <Button variant="outline" onClick={handleLogout} className="border-gray-300 text-sm">
                로그아웃
              </Button>
            </nav>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-2xl tracking-tight font-normal">
            StyleFlow
          </Link>

          {/* 데스크탑 */}
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-sm hover:text-gray-600 transition-colors">
              소개
            </Link>

            {user ? (
              <>
                <Link href="/my-home" className="text-sm hover:text-gray-600 transition-colors">
                  마이홈
                </Link>
                <span className="text-sm text-gray-500">{user.nickname}님</span>
                <Button
                  variant="outline"
                  onClick={handleLogout}
                  className="border-gray-300 text-sm"
                >
                  로그아웃
                </Button>
                <Button
                  onClick={() => router.push('/upload')}
                  className="bg-black text-white hover:bg-gray-800"
                >
                  분석 시작
                </Button>
              </>
            ) : (
              <>
                <Link href="/login" className="text-sm hover:text-gray-600 transition-colors">
                  로그인
                </Link>
                <Button
                  onClick={() => router.push('/signup')}
                  className="bg-black text-white hover:bg-gray-800"
                >
                  회원가입
                </Button>
              </>
            )}
          </nav>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* 모바일 메뉴 */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <nav className="flex flex-col gap-4">
              <Link
                href="/"
                className="text-sm hover:text-gray-600 transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                소개
              </Link>

              {user ? (
                <>
                  <Link
                    href="/my-home"
                    className="text-sm hover:text-gray-600 transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    마이홈
                  </Link>
                  <span className="text-sm text-gray-500">{user.nickname}님</span>
                  <Button
                    variant="outline"
                    onClick={() => { handleLogout(); setMobileMenuOpen(false); }}
                    className="border-gray-300"
                  >
                    로그아웃
                  </Button>
                  <Button
                    onClick={() => { router.push('/upload'); setMobileMenuOpen(false); }}
                    className="bg-black text-white hover:bg-gray-800"
                  >
                    분석 시작
                  </Button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="text-sm hover:text-gray-600 transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    로그인
                  </Link>
                  <Button
                    onClick={() => { router.push('/signup'); setMobileMenuOpen(false); }}
                    className="bg-black text-white hover:bg-gray-800"
                  >
                    회원가입
                  </Button>
                </>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
