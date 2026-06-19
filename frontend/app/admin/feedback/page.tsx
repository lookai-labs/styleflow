'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import api from '@/lib/api';

type Feedback = {
  id: number;
  user_nickname: string;
  target_type: 'hair' | 'makeup';
  user_chat: string | null;
  ai_chat: string | null;
  simulation_result: number | null;
  created_at: string;
};

function FeedbackTable({ items }: { items: Feedback[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-gray-400 py-6 text-center">채팅 기록이 없습니다.</p>;
  }

  return (
    <Card>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 text-gray-500">
            <th className="text-left px-4 py-3 font-medium w-12">ID</th>
            <th className="text-left px-4 py-3 font-medium w-28">유저</th>
            <th className="text-left px-4 py-3 font-medium w-24">타입</th>
            <th className="text-left px-4 py-3 font-medium">유저 메시지</th>
            <th className="text-left px-4 py-3 font-medium">AI 응답</th>
            <th className="text-left px-4 py-3 font-medium w-20">결과ID</th>
            <th className="text-left px-4 py-3 font-medium w-28">날짜</th>
          </tr>
        </thead>
        <tbody>
          {items.map((f) => (
            <tr key={f.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-gray-400">{f.id}</td>
              <td className="px-4 py-3 font-medium">{f.user_nickname}</td>
              <td className="px-4 py-3">
                <span className={`text-xs px-2 py-0.5 rounded-full ${f.target_type === 'hair' ? 'bg-blue-50 text-blue-600' : 'bg-pink-50 text-pink-600'}`}>
                  {f.target_type === 'hair' ? '헤어' : '메이크업'}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{f.user_chat ?? '-'}</td>
              <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{f.ai_chat ?? '-'}</td>
              <td className="px-4 py-3 text-gray-500">{f.simulation_result ?? '-'}</td>
              <td className="px-4 py-3 text-gray-500">{f.created_at.slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export default function FeedbackPage() {
  const [all, setAll] = useState<Feedback[]>([]);
  const [hair, setHair] = useState<Feedback[]>([]);
  const [makeup, setMakeup] = useState<Feedback[]>([]);

  useEffect(() => {
    api.get('/admin/feedback/').then((r) => setAll(r.data.results ?? r.data));
    api.get('/admin/feedback/?target_type=hair').then((r) => setHair(r.data.results ?? r.data));
    api.get('/admin/feedback/?target_type=makeup').then((r) => setMakeup(r.data.results ?? r.data));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">피드백 관리</h1>
      <Tabs defaultValue="all">
        <TabsList className="mb-6">
          <TabsTrigger value="all">전체 ({all.length})</TabsTrigger>
          <TabsTrigger value="hair">헤어 ({hair.length})</TabsTrigger>
          <TabsTrigger value="makeup">메이크업 ({makeup.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="all"><FeedbackTable items={all} /></TabsContent>
        <TabsContent value="hair"><FeedbackTable items={hair} /></TabsContent>
        <TabsContent value="makeup"><FeedbackTable items={makeup} /></TabsContent>
      </Tabs>
    </div>
  );
}
