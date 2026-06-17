'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import api from '@/lib/api';

type Mapping = {
  id: number;
  user_nickname: string;
  type: 'hair' | 'makeup' | 'ootd';
  style_name: string;
  created_at: string;
};

const TYPE_LABEL: Record<string, string> = {
  hair: '헤어', makeup: '메이크업', ootd: 'OOTD',
};

const TYPE_COLOR: Record<string, string> = {
  hair: 'bg-blue-50 text-blue-600',
  makeup: 'bg-pink-50 text-pink-600',
  ootd: 'bg-purple-50 text-purple-600',
};

function MappingTable({ items }: { items: Mapping[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-gray-400 py-6 text-center">추천 결과가 없습니다.</p>;
  }

  return (
    <Card>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 text-gray-500">
            <th className="text-left px-4 py-3 font-medium w-12">ID</th>
            <th className="text-left px-4 py-3 font-medium w-28">유저</th>
            <th className="text-left px-4 py-3 font-medium w-24">타입</th>
            <th className="text-left px-4 py-3 font-medium">스타일명</th>
            <th className="text-left px-4 py-3 font-medium w-28">날짜</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-gray-400">{m.id}</td>
              <td className="px-4 py-3 font-medium">{m.user_nickname}</td>
              <td className="px-4 py-3">
                <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLOR[m.type] ?? 'bg-gray-100 text-gray-600'}`}>
                  {TYPE_LABEL[m.type] ?? m.type}
                </span>
              </td>
              <td className="px-4 py-3">{m.style_name}</td>
              <td className="px-4 py-3 text-gray-500">{m.created_at.slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export default function MappingsPage() {
  const [all, setAll] = useState<Mapping[]>([]);
  const [hair, setHair] = useState<Mapping[]>([]);
  const [makeup, setMakeup] = useState<Mapping[]>([]);
  const [ootd, setOotd] = useState<Mapping[]>([]);

  useEffect(() => {
    api.get('/admin/style-mappings/').then((r) => setAll(r.data.results ?? r.data));
  }, []);

  useEffect(() => {
    setHair(all.filter((m) => m.type === 'hair'));
    setMakeup(all.filter((m) => m.type === 'makeup'));
    setOotd(all.filter((m) => m.type === 'ootd'));
  }, [all]);

  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">추천 결과 검수</h1>
      <Tabs defaultValue="all">
        <TabsList className="mb-6">
          <TabsTrigger value="all">전체 ({all.length})</TabsTrigger>
          <TabsTrigger value="hair">헤어 ({hair.length})</TabsTrigger>
          <TabsTrigger value="makeup">메이크업 ({makeup.length})</TabsTrigger>
          <TabsTrigger value="ootd">OOTD ({ootd.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="all"><MappingTable items={all} /></TabsContent>
        <TabsContent value="hair"><MappingTable items={hair} /></TabsContent>
        <TabsContent value="makeup"><MappingTable items={makeup} /></TabsContent>
        <TabsContent value="ootd"><MappingTable items={ootd} /></TabsContent>
      </Tabs>
    </div>
  );
}
