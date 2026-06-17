"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Sparkles, ArrowRight } from "lucide-react";

export default function SimulationPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl tracking-tight mb-4">AI 시뮬레이션</h1>
          <p className="text-lg text-gray-600">추천 스타일을 이미지로 미리 확인하고 Before / After를 비교해보세요.</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-12 lg:items-stretch">
          <Card className="p-8 border border-gray-200 bg-white flex flex-col h-full">
            <h2 className="text-2xl mb-6">이용방법</h2>
            <div className="space-y-3 text-sm text-gray-600">
              {[
                "원하는 분석 유형을 선택하세요 (헤어 & 메이크업 또는 코디)",
                "사진을 업로드하고 AI 분석을 시작하세요",
                "추천 카드를 선택하거나 참고 이미지를 업로드하세요",
                "AI 시뮬레이션 이미지를 생성하고 Before / After를 확인하세요",
              ].map((step, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-black text-white rounded-full flex items-center justify-center text-xs">{idx + 1}</span>
                  <p>{step}</p>
                </div>
              ))}
            </div>
          </Card>

          <div className="space-y-6 flex flex-col h-full">
            <Card className="p-8 border border-gray-200 bg-white flex-1">
              <h2 className="text-2xl mb-6">시작하기</h2>
              <div className="space-y-4">
                <Button onClick={() => router.push("/upload?type=face")} className="w-full bg-white text-black border-2 border-black hover:bg-gray-50 justify-between">
                  <span>헤어 &amp; 메이크업 분석 후 시뮬레이션</span>
                  <ArrowRight className="w-5 h-5" />
                </Button>
                <Button onClick={() => router.push("/upload?type=outfit")} className="w-full bg-white text-black border-2 border-black hover:bg-gray-50 justify-between">
                  <span>코디 분석 후 시뮬레이션</span>
                  <ArrowRight className="w-5 h-5" />
                </Button>
                <Button onClick={() => router.push("/my-home")} className="w-full bg-white text-black border-2 border-black hover:bg-gray-50 justify-between">
                  <span>마이홈에서 시뮬레이션</span>
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </div>
            </Card>

            <Card className="p-8 border border-gray-200 bg-white flex-1">
              <h2 className="text-2xl mb-4">AI 시뮬레이션이란?</h2>
              <ul className="space-y-3 text-gray-600">
                {[
                  "추천받은 스타일을 이미지로 미리 확인",
                  "참고 이미지를 업로드해 원하는 스타일 적용",
                  "Before / After 비교로 변화 확인",
                  "실제 시도 전 가상으로 스타일 체험",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <Sparkles className="w-5 h-5 mt-0.5 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>

        <div className="mb-12">
          <h2 className="text-3xl mb-8 text-center">AI 시뮬레이션 예시</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { image: "https://images.unsplash.com/photo-1619218533116-f050e7d91d91?w=800", title: "헤어스타일 시뮬레이션", description: "레이어드 웨이브 스타일 적용" },
              { image: "https://images.unsplash.com/photo-1619749623747-c256b910961a?w=800", title: "메이크업 시뮬레이션", description: "웜 코랄 메이크업 적용" },
              { image: "https://images.unsplash.com/photo-1595331292515-a6449d5215e9?w=800", title: "코디 시뮬레이션", description: "미니멀 캐주얼 스타일 적용" },
            ].map((sample, idx) => (
              <Card key={idx} className="overflow-hidden border border-gray-200 bg-white">
                <img src={sample.image} alt={sample.title} className="w-full h-64 object-cover" />
                <div className="p-4">
                  <h3 className="font-medium mb-1">{sample.title}</h3>
                  <p className="text-sm text-gray-600">{sample.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>

        <div className="text-center">
          <Button onClick={() => router.push("/upload")} className="bg-black text-white hover:bg-gray-800 text-base px-12 py-6">
            <Sparkles className="mr-2 h-5 w-5" />AI 분석 시작하기
          </Button>
        </div>
      </div>
    </div>
  );
}
