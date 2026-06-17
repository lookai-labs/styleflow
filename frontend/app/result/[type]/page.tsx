"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Check } from "lucide-react";
import { StylingSelectionModal } from "@/components/StylingSelectionModal";

/* ── 분석 결과 데이터 (하드코딩) ── */
const ANALYSIS = {
  faceShape: "둥근형",
  faceDesc: "부드럽고 온화한 인상으로, 레이어드 스타일과 옆 볼륨 헤어가 얼굴 균형을 보완합니다.",
  skinTone: "웜톤",
  skinDesc: "따뜻한 황금빛 피부톤으로 코랄, 베이지, 웜 브라운 계열이 자연스럽게 어울립니다.",
  colors: [
    { name: "웜 코랄",  hex: "#D4826A" },
    { name: "베이지",   hex: "#C9A882" },
    { name: "웜 브라운",hex: "#7A5238" },
    { name: "아이보리", hex: "#EDE0C8" },
  ],
};

/* ── 추천 스타일 미리보기 데이터 ── */
const RECOMMENDATIONS = {
  makeup: [
    { name: "웜 코랄 메이크업", desc: "따뜻하고 생기있는 코랄 톤",  image: "/reference/makeup/MS1.png" },
    { name: "소프트 뉴트럴",    desc: "자연스러운 베이지 톤",        image: "/reference/makeup/MS2.png" },
    { name: "로즈 글로우",      desc: "은은한 로즈 톤 글로우",       image: "/reference/makeup/MS3.png" },
  ],
  hair: [
    { name: "레이어드 웨이브",  desc: "부드러운 레이어와 자연스러운 웨이브", image: "https://images.unsplash.com/photo-1522337660859-02fbefca4702?w=800" },
    { name: "소프트 볼륨",      desc: "볼륨감 있는 레이어드 스타일",         image: "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800" },
    { name: "롱 스트레이트",    desc: "깔끔하고 단정한 롱 스트레이트",       image: "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=800" },
  ],
};

const SECTION_LABELS = { makeup: "메이크업", hair: "헤어" } as const;

/* ────────────────────────────── */

export default function ResultPage() {
  const router = useRouter();
  const params = useParams();
  const type = params.type as "face" | "outfit";
  const [showStylingSelection, setShowStylingSelection] = useState(false);
  const [faceImage, setFaceImage] = useState<string>("");

  useEffect(() => {
    window.scrollTo(0, 0);
    const saved = localStorage.getItem("styleflow_face_image");
    if (saved) setFaceImage(saved);
  }, []);

  const handleStylingConfirm = (selected: { makeup: boolean; hair: boolean }) => {
    localStorage.removeItem("styleflow_makeup_results");
    localStorage.removeItem("styleflow_selected_id");
    const styles = (["makeup", "hair"] as const)
      .filter((k) => selected[k])
      .join(",");
    router.push(`/simulation-flow?styles=${styles}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">

        {/* ══════════════════════════════════
            1. 분석 결과
        ══════════════════════════════════ */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <h1 className="text-4xl lg:text-5xl tracking-tight">분석 결과</h1>
            <Badge className="bg-black text-white flex items-center gap-1.5 px-3 py-1">
              <Check className="w-3.5 h-3.5" />
              AI 분석 완료
            </Badge>
          </div>

          <div className="grid lg:grid-cols-5 gap-6">
            {/* 업로드 사진 */}
            <div className="lg:col-span-2">
              <Card className="overflow-hidden border border-gray-200">
                <img
                  src={faceImage || "/reference/makeup/MS1.png"}
                  alt="업로드된 사진"
                  className="w-full h-80 object-cover"
                />
                <div className="p-3 bg-gray-50 text-center">
                  <span className="text-xs text-gray-400">업로드된 원본 사진</span>
                </div>
              </Card>
            </div>

            {/* 분석 결과 상세 */}
            <div className="lg:col-span-3 flex flex-col gap-4">

              {/* 얼굴형 */}
              <Card className="p-6 border border-gray-200 bg-white">
                <div className="flex items-start justify-between mb-3">
                  <span className="text-xs font-semibold tracking-widest text-gray-400 uppercase">얼굴형</span>
                  <span className="text-lg font-medium">{ANALYSIS.faceShape}</span>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">{ANALYSIS.faceDesc}</p>
              </Card>

              {/* 피부톤 */}
              <Card className="p-6 border border-gray-200 bg-white">
                <div className="flex items-start justify-between mb-3">
                  <span className="text-xs font-semibold tracking-widest text-gray-400 uppercase">피부톤</span>
                  <span className="text-lg font-medium">{ANALYSIS.skinTone}</span>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed mb-4">{ANALYSIS.skinDesc}</p>

                {/* 퍼스널 컬러 칩 */}
                <div className="border-t border-gray-100 pt-4">
                  <span className="text-xs text-gray-400 mb-3 block">추천 컬러 팔레트</span>
                  <div className="flex gap-3">
                    {ANALYSIS.colors.map((color) => (
                      <div key={color.name} className="flex flex-col items-center gap-1.5">
                        <div
                          className="w-9 h-9 rounded-full border border-gray-200 shadow-sm"
                          style={{ backgroundColor: color.hex }}
                        />
                        <span className="text-xs text-gray-500 whitespace-nowrap">{color.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>

            </div>
          </div>
        </section>

        {/* ══════════════════════════════════
            2. 추천 스타일 미리보기
        ══════════════════════════════════ */}
        <section>
          <div className="mb-8">
            <h2 className="text-3xl tracking-tight mb-2">AI 추천 스타일</h2>
            <p className="text-gray-500">분석 결과를 바탕으로 어울리는 스타일을 미리 확인하세요.</p>
          </div>

          <div className="space-y-10">
            {(["makeup", "hair"] as const).map((category) => (
              <div key={category}>
                {/* 카테고리 레이블 */}
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-lg font-medium">{SECTION_LABELS[category]}</span>
                  <div className="flex-1 h-px bg-gray-200" />
                </div>

                {/* 추천 카드 3장 */}
                <div className="grid grid-cols-3 gap-4">
                  {RECOMMENDATIONS[category].map((item, idx) => (
                    <Card
                      key={idx}
                      className="overflow-hidden border border-gray-200 bg-white group"
                    >
                      <div className="relative overflow-hidden">
                        <img
                          src={item.image}
                          alt={item.name}
                          className="w-full h-56 object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                      </div>
                      <div className="p-4">
                        <h3 className="font-medium text-sm mb-0.5">{item.name}</h3>
                        <p className="text-xs text-gray-400">{item.desc}</p>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ══════════════════════════════════
            3. 시뮬레이션 시작 CTA
        ══════════════════════════════════ */}
        <section>
          <Card className="p-10 border-2 border-black bg-white text-center">
            <h2 className="text-2xl mb-2">이 스타일로 시뮬레이션 해볼까요?</h2>
            <p className="text-gray-500 mb-8">원하는 항목을 선택하면 AI가 단계별로 시뮬레이션 이미지를 생성합니다.</p>
            <Button
              onClick={() => setShowStylingSelection(true)}
              size="lg"
              className="bg-black text-white hover:bg-gray-800 text-base px-14 py-6"
            >
              <Sparkles className="mr-2 h-5 w-5" />
              시뮬레이션 시작하기
            </Button>
          </Card>
        </section>

      </div>

      <StylingSelectionModal
        open={showStylingSelection}
        onClose={() => setShowStylingSelection(false)}
        onConfirm={handleStylingConfirm}
        type={type}
      />
    </div>
  );
}
