'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import api from '@/lib/api';

type User = {
  id: number;
  nickname: string;
  gender: string;
  role: string;
  created_at: string;
};

type AnalysisSession = {
  id: number;
  face_shape: string | null;
  face_point: string | null;
  skin_tone: string | null;
  created_at: string;
};

const GENDER_LABEL: Record<string, string> = { male: '남성', female: '여성' };
const FACE_SHAPE_LABEL: Record<string, string> = {
  oval: '달걀형', round: '둥근형', square: '각진형', oblong: '긴형', heart: '하트형',
};
const SKIN_TONE_LABEL: Record<string, string> = {
  spring: '봄', summer: '여름', fall: '가을', winter: '겨울',
};
const FACE_POINT_LABEL: Record<string, string> = {
  upper: '상정', middle: '중정', lower: '하정', golden: '황금비',
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [selected, setSelected] = useState<User | null>(null);
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  useEffect(() => {
    api.get('/admin/users/').then((r) => setUsers(r.data.results ?? r.data));
  }, []);

  const openSessions = async (user: User) => {
    setSelected(user);
    setLoadingSessions(true);
    setSessions([]);
    try {
      const r = await api.get(`/admin/analyses/?user_id=${user.id}`);
      setSessions(r.data.results ?? r.data);
    } finally {
      setLoadingSessions(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">사용자 관리</h1>

      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-gray-500">
              <th className="text-left px-4 py-3 font-medium w-12">ID</th>
              <th className="text-left px-4 py-3 font-medium">닉네임</th>
              <th className="text-left px-4 py-3 font-medium w-20">성별</th>
              <th className="text-left px-4 py-3 font-medium w-20">역할</th>
              <th className="text-left px-4 py-3 font-medium">가입일</th>
              <th className="px-4 py-3 w-28" />
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-400">사용자가 없습니다.</td></tr>
            )}
            {users.map((u) => (
              <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400">{u.id}</td>
                <td className="px-4 py-3 font-medium">{u.nickname}</td>
                <td className="px-4 py-3 text-gray-500">{GENDER_LABEL[u.gender] ?? u.gender}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${u.role === 'admin' ? 'bg-black text-white' : 'bg-gray-100 text-gray-600'}`}>
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{u.created_at.slice(0, 10)}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => openSessions(u)}
                    className="text-xs px-3 py-1.5 rounded border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    분석 기록
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selected?.nickname}님의 분석 기록</DialogTitle>
          </DialogHeader>
          {loadingSessions ? (
            <p className="text-sm text-gray-400 py-4 text-center">불러오는 중...</p>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">분석 기록이 없습니다.</p>
          ) : (
            <table className="w-full text-sm mt-2">
              <thead>
                <tr className="border-b border-gray-100 text-gray-500">
                  <th className="text-left py-2 font-medium">날짜</th>
                  <th className="text-left py-2 font-medium">얼굴형</th>
                  <th className="text-left py-2 font-medium">얼굴 비율</th>
                  <th className="text-left py-2 font-medium">피부톤</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id} className="border-b border-gray-50">
                    <td className="py-2 text-gray-500">{s.created_at.slice(0, 10)}</td>
                    <td className="py-2">{s.face_shape ? FACE_SHAPE_LABEL[s.face_shape] ?? s.face_shape : '-'}</td>
                    <td className="py-2">{s.face_point ? FACE_POINT_LABEL[s.face_point] ?? s.face_point : '-'}</td>
                    <td className="py-2">{s.skin_tone ? SKIN_TONE_LABEL[s.skin_tone] ?? s.skin_tone : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
