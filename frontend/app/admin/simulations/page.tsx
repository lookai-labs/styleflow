'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Trash2 } from 'lucide-react';
import api from '@/lib/api';

type Simulation = {
  id: number;
  user_nickname: string;
  is_saved: boolean;
  generated_image_path: string | null;
  created_at: string;
};

export default function SimulationsPage() {
  const [items, setItems] = useState<Simulation[]>([]);

  const load = () => api.get('/admin/simulation-results/').then((r) => setItems(r.data.results ?? r.data));

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('시뮬레이션 결과를 삭제하시겠습니까?')) return;
    await api.delete(`/admin/simulation-results/${id}/`);
    load();
  };

  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">시뮬레이션 결과 관리</h1>

      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-gray-500">
              <th className="text-left px-4 py-3 font-medium w-12">ID</th>
              <th className="text-left px-4 py-3 font-medium w-28">유저</th>
              <th className="text-left px-4 py-3 font-medium">날짜</th>
              <th className="text-left px-4 py-3 font-medium w-20">저장여부</th>
              <th className="text-left px-4 py-3 font-medium">이미지 경로</th>
              <th className="px-4 py-3 w-16" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-400">결과가 없습니다.</td></tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400">{item.id}</td>
                <td className="px-4 py-3 font-medium">{item.user_nickname}</td>
                <td className="px-4 py-3 text-gray-500">{item.created_at.slice(0, 10)}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${item.is_saved ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'}`}>
                    {item.is_saved ? '저장됨' : '미저장'}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 max-w-xs truncate">{item.generated_image_path ?? '-'}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
