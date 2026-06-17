'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRequireAdmin } from '@/hooks/useRequireAdmin';

const NAV_ITEMS = [
  { href: '/admin', label: '대시보드' },
  { href: '/admin/users', label: '사용자 관리' },
  { href: '/admin/styles', label: '스타일 관리' },
  { href: '/admin/feedback', label: '피드백 관리' },
  { href: '/admin/sessions', label: '세션 검수' },
  { href: '/admin/mappings', label: '추천 결과 검수' },
  { href: '/admin/simulations', label: '시뮬레이션 결과' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAdmin = useRequireAdmin();

  if (!isAdmin) return null;

  return (
    <div className="flex min-h-[calc(100vh-64px)] bg-gray-50">
      <aside className="w-52 shrink-0 bg-white border-r border-gray-200 p-5 flex flex-col gap-1">
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
          관리자 메뉴
        </div>
        {NAV_ITEMS.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`px-3 py-2 rounded-md text-sm transition-colors ${
              pathname === href
                ? 'bg-black text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            {label}
          </Link>
        ))}
      </aside>

      <main className="flex-1 p-8 min-w-0">{children}</main>
    </div>
  );
}
