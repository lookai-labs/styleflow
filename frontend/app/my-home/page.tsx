"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trash2, ChevronRight, Download } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";

type AppliedStyle = {
  type: "makeup" | "hair" | "outfit";
  name: string;
};

type SavedResult = {
  id: string;
  date: string;
  beforeImage: string;
  afterImage: string;
  appliedStyles: AppliedStyle[];
};

const STYLE_LABEL: Record<AppliedStyle["type"], string> = {
  makeup: "메이크업",
  hair: "헤어",
  outfit: "코디",   // API 응답 호환성 유지용
};

const STYLE_SUFFIX: Partial<Record<AppliedStyle["type"], string>> = {
  makeup: "메이크업",
  hair: "헤어",
};

const getDisplayName = (style: AppliedStyle): string => {
  const suffix = STYLE_SUFFIX[style.type];
  if (!suffix || style.name.endsWith(suffix)) return style.name;
  return `${style.name} ${suffix}`;
};


export default function MyHomePage() {
  const router = useRouter();
  const authorized = useRequireAuth();
  const [results, setResults] = useState<SavedResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authorized) return;
    api.get("/saved-results/")
      .then((res) => {
        const data = res.data?.results ?? res.data;
        setResults(Array.isArray(data) ? data : []);
      })
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [authorized]);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/saved-results/${id}/`);
    } catch {}
    setResults((prev) => prev.filter((r) => r.id !== id));
    toast.success("결과가 삭제되었습니다");
  };

  const handleSave = async (afterImage: string, id: string) => {
    try {
      const res = await fetch(afterImage);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `styleflow-simulation-${id}.jpg`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("이미지가 저장되었습니다");
    } catch {
      toast.error("이미지 저장에 실패했습니다");
    }
  };

  if (!authorized) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="mb-10">
          <h1 className="text-4xl lg:text-5xl tracking-tight mb-3">마이홈</h1>
          <p className="text-lg text-gray-600">저장된 AI 시뮬레이션 결과를 확인하세요.</p>
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-400">불러오는 중...</div>
        ) : results.length === 0 ? (
          <Card className="p-16 border border-gray-200 bg-white text-center">
            <div className="max-w-md mx-auto space-y-4">
              <h3 className="text-2xl">저장된 시뮬레이션 결과가 없습니다.</h3>
              <p className="text-gray-600">시뮬레이션을 완료하면 결과가 이곳에 저장됩니다.</p>
              <Button
                onClick={() => router.push("/upload")}
                className="bg-black text-white hover:bg-gray-800 mt-4"
              >
                스타일 분석 시작하기
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {results.map((result) => (
              <Card key={result.id} className="border border-gray-200 bg-white overflow-hidden flex flex-col">

                {/* Before / After 이미지 영역 */}
                <div className="relative flex h-72">
                  {/* Before — 좁은 왼쪽 */}
                  <div className="relative w-2/5 flex-shrink-0">
                    <img
                      src={result.beforeImage}
                      alt="Before"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/20" />
                    <span className="absolute top-3 left-3 text-xs font-semibold tracking-widest text-white/90 uppercase">
                      Before
                    </span>
                  </div>

                  {/* 구분 화살표 */}
                  <div className="absolute left-2/5 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10
                                  w-7 h-7 rounded-full bg-white flex items-center justify-center shadow-md">
                    <ChevronRight className="w-4 h-4 text-black" />
                  </div>

                  {/* After — 넓은 오른쪽 */}
                  <div className="relative flex-1">
                    <img
                      src={result.afterImage}
                      alt="After"
                      className="w-full h-full object-cover"
                    />
                    <span className="absolute top-3 left-4 text-xs font-semibold tracking-widest text-white/90 uppercase">
                      After
                    </span>
                  </div>
                </div>

                {/* 카드 정보 */}
                <div className="p-5 flex flex-col flex-1">
                  {/* 적용 스타일 */}
                  <div className="space-y-1.5 mb-4 flex-1">
                    {result.appliedStyles.map((style) => (
                      <div key={style.type} className="flex items-center gap-2 text-sm">
                        <span className="text-xs text-gray-400 w-12 flex-shrink-0">{STYLE_LABEL[style.type]}</span>
                        <span className="font-medium text-gray-800">{getDisplayName(style)}</span>
                      </div>
                    ))}
                  </div>

                  {/* 날짜 + 버튼 */}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-400">
                      {new Date(result.date).toLocaleDateString("ko-KR", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="border border-gray-200 text-gray-500 hover:border-black hover:text-black transition-colors text-xs"
                        onClick={() => handleSave(result.afterImage, result.id)}
                      >
                        <Download className="h-3 w-3 mr-1" />
                        저장
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="border border-gray-200 text-gray-400 hover:border-red-400 hover:text-red-500 hover:bg-red-50 transition-colors text-xs"
                        onClick={() => handleDelete(result.id)}
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        삭제
                      </Button>
                    </div>
                  </div>
                </div>

              </Card>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
