'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import api from '@/lib/api';

type Session = {
  id: number;
  user_nickname: string;
  face_shape: string | null;
  face_point: string | null;
  skin_tone: string | null;
  ratio_face_wh: number | null;
  ratio_jaw_cheek: number | null;
  created_at: string;
};

const FACE_SHAPE_LABEL: Record<string, string> = {
  oval: '달걀형', round: '둥근형', square: '각진형', oblong: '긴형', heart: '하트형',
};
const SKIN_TONE_LABEL: Record<string, string> = {
  spring: '봄', summer: '여름', fall: '가을', winter: '겨울',
};
const FACE_POINT_LABEL: Record<string, string> = {
  upper: '상정', middle: '중정', lower: '하정', golden: '황금비',
};

function isAnomaly(s: Session) {
  return !s.face_shape || !s.skin_tone || !s.face_point;
}

function SessionTable({ items }: { items: Session[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-gray-400 py-6 text-center">세션이 없습니다.</p>;
  }

  return (
    <Card>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 text-gray-500">
            <th className="text-left px-4 py-3 font-medium w-12">ID</th>
            <th className="text-left px-4 py-3 font-medium w-28">유저</th>
            <th className="text-left px-4 py-3 font-medium">날짜</th>
            <th className="text-left px-4 py-3 font-medium">얼굴형</th>
            <th className="text-left px-4 py-3 font-medium">얼굴비율</th>
            <th className="text-left px-4 py-3 font-medium">피부톤</th>
            <th className="text-left px-4 py-3 font-medium w-20">상태</th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) => {
            const anomaly = isAnomaly(s);
            return (
              <tr key={s.id} className={`border-b border-gray-50 transition-colors ${anomaly ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'}`}>
                <td className="px-4 py-3 text-gray-400">{s.id}</td>
                <td className="px-4 py-3 font-medium">{s.user_nickname}</td>
                <td className="px-4 py-3 text-gray-500">{s.created_at.slice(0, 10)}</td>
                <td className="px-4 py-3">{s.face_shape ? FACE_SHAPE_LABEL[s.face_shape] ?? s.face_shape : <span className="text-red-400">미분석</span>}</td>
                <td className="px-4 py-3">{s.face_point ? FACE_POINT_LABEL[s.face_point] ?? s.face_point : <span className="text-red-400">미분석</span>}</td>
                <td className="px-4 py-3">{s.skin_tone ? SKIN_TONE_LABEL[s.skin_tone] ?? s.skin_tone : <span className="text-red-400">미분석</span>}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${anomaly ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                    {anomaly ? '이상' : '정상'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Card>
  );
}

export default function SessionsPage() {
  const [all, setAll] = useState<Session[]>([]);
  const [anomalies, setAnomalies] = useState<Session[]>([]);

  useEffect(() => {
    api.get('/admin/analyses/').then((r) => setAll(r.data.results ?? r.data));
    api.get('/admin/analyses/?anomaly=true').then((r) => setAnomalies(r.data.results ?? r.data));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">분석 세션 검수</h1>
      <Tabs defaultValue="all">
        <TabsList className="mb-6">
          <TabsTrigger value="all">전체 ({all.length})</TabsTrigger>
          <TabsTrigger value="anomaly">
            이상 데이터 ({anomalies.length})
          </TabsTrigger>
        </TabsList>
        <TabsContent value="all"><SessionTable items={all} /></TabsContent>
        <TabsContent value="anomaly"><SessionTable items={anomalies} /></TabsContent>
      </Tabs>
    </div>
  );
}
