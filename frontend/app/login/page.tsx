'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoggedIn, user } = useAuth();
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ nickname?: string; password?: string; general?: string }>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn) router.replace(user?.role === 'admin' ? '/admin' : '/');
  }, [isLoggedIn, user, router]);

  const validate = () => {
    const e: typeof errors = {};
    if (!nickname.trim()) e.nickname = '아이디를 입력해주세요.';
    if (!password) e.password = '비밀번호를 입력해주세요.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await api.post('/auth/login/', { nickname, password });
      login(res.data.access, res.data.refresh, res.data.user);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setErrors({ general: msg ?? '로그인에 실패했습니다.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl tracking-tight mb-2">로그인</h1>
          <p className="text-gray-600">StyleFlow 서비스를 이용하려면 로그인이 필요합니다</p>
        </div>

        <Card className="p-8 border border-gray-200 bg-white">
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-1.5">아이디</label>
              <Input
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="아이디를 입력하세요"
                className={errors.nickname ? 'border-red-500 focus-visible:ring-red-500' : ''}
              />
              {errors.nickname && <p className="text-red-500 text-sm mt-1">{errors.nickname}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">비밀번호</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="비밀번호를 입력하세요"
                className={errors.password ? 'border-red-500 focus-visible:ring-red-500' : ''}
              />
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
            </div>

            {errors.general && (
              <p className="text-red-500 text-sm text-center bg-red-50 py-2 px-3 rounded">
                {errors.general}
              </p>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-black text-white hover:bg-gray-800 py-5 text-base"
            >
              {loading ? '로그인 중...' : '로그인'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            계정이 없으신가요?{' '}
            <Link href="/signup" className="font-medium text-black underline underline-offset-2">
              회원가입
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
