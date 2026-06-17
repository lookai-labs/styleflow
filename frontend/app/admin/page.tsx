'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import api from '@/lib/api';

type DashboardData = {
  total_users: number;
  total_sessions: number;
  skin_tone_distribution: { skin_tone: string; count: number }[];
  face_shape_distribution: { face_shape: string; count: number }[];
};

const SKIN_TONE_LABELS: Record<string, string> = {
  spring: '봄(Spring)',
  summer: '여름(Summer)',
  fall: '가을(Fall)',
  winter: '겨울(Winter)',
};

const FACE_SHAPE_LABELS: Record<string, string> = {
  oval: '달걀형(Oval)',
  round: '둥근형(Round)',
  square: '각진형(Square)',
  oblong: '긴형(Oblong)',
  heart: '하트형(Heart)',
};

function DistBar({ label, count, max }: { label: string; count: number; max: number }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-400">{count}명</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-2 bg-black rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.get('/admin/dashboard/')
      .then((res) => setData(res.data))
      .catch(() => setError(true));
  }, []);

  const maxSkin = data ? Math.max(...data.skin_tone_distribution.map((d) => d.count), 1) : 1;
  const maxFace = data ? Math.max(...data.face_shape_distribution.map((d) => d.count), 1) : 1;

  if (error) return <p className="text-red-500">데이터를 불러오지 못했습니다.</p>;

  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">대시보드</h1>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <Card className="p-6">
          <p className="text-sm text-gray-500 mb-1">전체 사용자</p>
          <p className="text-4xl font-medium">{data?.total_users ?? '—'}</p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-gray-500 mb-1">전체 분석 세션</p>
          <p className="text-4xl font-medium">{data?.total_sessions ?? '—'}</p>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card className="p-6">
          <p className="font-medium mb-4">피부톤 분포</p>
          {data?.skin_tone_distribution.length === 0 && (
            <p className="text-sm text-gray-400">데이터 없음</p>
          )}
          <div className="space-y-3">
            {data?.skin_tone_distribution.map((item) => (
              <DistBar
                key={item.skin_tone}
                label={SKIN_TONE_LABELS[item.skin_tone] ?? item.skin_tone}
                count={item.count}
                max={maxSkin}
              />
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <p className="font-medium mb-4">얼굴형 분포</p>
          {data?.face_shape_distribution.length === 0 && (
            <p className="text-sm text-gray-400">데이터 없음</p>
          )}
          <div className="space-y-3">
            {data?.face_shape_distribution.map((item) => (
              <DistBar
                key={item.face_shape}
                label={FACE_SHAPE_LABELS[item.face_shape] ?? item.face_shape}
                count={item.count}
                max={maxFace}
              />
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
