'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';

export default function SignupPage() {
  const router = useRouter();
  const { login, isLoggedIn } = useAuth();
  const [form, setForm] = useState({ nickname: '', password: '', passwordConfirm: '', gender: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn) router.replace('/');
  }, [isLoggedIn, router]);

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.nickname.trim()) e.nickname = '아이디를 입력해주세요.';
    if (!form.password) e.password = '비밀번호를 입력해주세요.';
    if (form.password && form.password !== form.passwordConfirm)
      e.passwordConfirm = '비밀번호가 일치하지 않습니다.';
    if (!form.gender) e.gender = '성별을 선택해주세요.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await api.post('/auth/register/', {
        nickname: form.nickname,
        password: form.password,
        gender: form.gender,
      });
      login(res.data.access, res.data.refresh, res.data.user);
      router.push('/');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error;
      setErrors({ general: msg ?? '회원가입에 실패했습니다.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl tracking-tight mb-2">회원가입</h1>
          <p className="text-gray-600">StyleFlow 멤버가 되어 스타일을 저장하세요</p>
        </div>

        <Card className="p-8 border border-gray-200 bg-white">
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-1.5">아이디</label>
              <Input
                value={form.nickname}
                onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                placeholder="사용할 아이디를 입력하세요"
                className={errors.nickname ? 'border-red-500 focus-visible:ring-red-500' : ''}
              />
              {errors.nickname && <p className="text-red-500 text-sm mt-1">{errors.nickname}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">비밀번호</label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="비밀번호를 입력하세요"
                className={errors.password ? 'border-red-500 focus-visible:ring-red-500' : ''}
              />
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">비밀번호 확인</label>
              <Input
                type="password"
                value={form.passwordConfirm}
                onChange={(e) => setForm({ ...form, passwordConfirm: e.target.value })}
                placeholder="비밀번호를 다시 입력하세요"
                className={errors.passwordConfirm ? 'border-red-500 focus-visible:ring-red-500' : ''}
              />
              {errors.passwordConfirm && (
                <p className="text-red-500 text-sm mt-1">{errors.passwordConfirm}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">성별</label>
              <div className="flex gap-8">
                {[{ value: 'male', label: '남성' }, { value: 'female', label: '여성' }].map(
                  ({ value, label }) => (
                    <label key={value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="gender"
                        value={value}
                        checked={form.gender === value}
                        onChange={(e) => setForm({ ...form, gender: e.target.value })}
                        className="w-4 h-4 accent-black"
                      />
                      <span className="text-sm">{label}</span>
                    </label>
                  )
                )}
              </div>
              {errors.gender && <p className="text-red-500 text-sm mt-1">{errors.gender}</p>}
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
              {loading ? '가입 중...' : '회원가입'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            이미 계정이 있으신가요?{' '}
            <Link href="/login" className="font-medium text-black underline underline-offset-2">
              로그인
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
