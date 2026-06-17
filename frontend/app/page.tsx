"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Sparkles, User, Shirt, Palette, Eye, Scissors, Wand2,
  Upload, MessageSquare, Save, ImagePlay, ArrowLeftRight, Paintbrush,
} from "lucide-react";

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <h1 className="text-5xl lg:text-6xl tracking-tight leading-tight">
              AI가 추천하고<br />
              미리 경험하는<br />
              나만의 스타일
            </h1>
            <p className="text-lg text-gray-600 leading-relaxed">
              StyleFlow는 얼굴형, 피부톤, 현재 스타일을 분석해 헤어, 메이크업, 코디를 추천하고 AI 시뮬레이션으로 직접 경험할 수 있습니다.
            </p>
            <div>
              <Button
                size="lg"
                onClick={() => router.push("/upload")}
                className="bg-black text-white hover:bg-gray-800 text-base px-12 py-6"
              >
                스타일 분석 시작하기
              </Button>
            </div>
          </div>
          <div className="relative h-[500px] lg:h-[600px]">
            <img
              src="https://images.unsplash.com/photo-1603189343302-e603f7add05a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb25vY2hyb21lJTIwZmFzaGlvbiUyMGVkaXRvcmlhbCUyMHBvcnRyYWl0fGVufDF8fHx8MTc3OTE3NDk5MHww&ixlib=rb-4.1.0&q=80&w=1080"
              alt="Fashion editorial"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* Feature Section */}
      <section className="bg-gray-50 py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl lg:text-5xl tracking-tight mb-12 text-center">
            AI가 분석할 수 있는 것은?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="p-8 lg:p-12 border border-gray-200 bg-white flex flex-col">
              <div className="flex items-center gap-3 mb-6">
                <User className="w-8 h-8" />
                <h3 className="text-2xl lg:text-3xl">헤어 &amp; 메이크업</h3>
              </div>
              <ul className="space-y-3 text-gray-600 flex-grow mb-6">
                {["얼굴형 분석","피부톤 분석","헤어스타일 추천","메이크업 추천","AI 시뮬레이션 생성"].map((item) => (
                  <li key={item} className="flex items-start gap-2"><span className="mt-1">•</span><span>{item}</span></li>
                ))}
              </ul>
              <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwbW9kZWwlMjBmYWNlJTIwcG9ydHJhaXR8ZW58MXx8fHwxNzc5MTc0OTkxfDA&ixlib=rb-4.1.0&q=80&w=1080" alt="Face analysis" className="w-full h-64 object-cover" />
            </Card>

            <Card className="p-8 lg:p-12 border border-gray-200 bg-white flex flex-col">
              <div className="flex items-center gap-3 mb-6">
                <Shirt className="w-8 h-8" />
                <h3 className="text-2xl lg:text-3xl">코디</h3>
              </div>
              <ul className="space-y-3 text-gray-600 flex-grow mb-6">
                {["전신 착장 분석","얼굴 영역 추출","피부톤 분석","컬러 분석","스타일 무드 분석","통합 스타일 추천","AI 시뮬레이션 이미지 생성"].map((item) => (
                  <li key={item} className="flex items-start gap-2"><span className="mt-1">•</span><span>{item}</span></li>
                ))}
              </ul>
              <img src="https://images.unsplash.com/photo-1627130697816-4d71dbfe6a5b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtaW5pbWFsJTIwZmFzaGlvbiUyMG91dGZpdCUyMHBob3RvZ3JhcGh5fGVufDF8fHx8MTc3OTE3NDk5MXww&ixlib=rb-4.1.0&q=80&w=1080" alt="Outfit analysis" className="w-full h-64 object-cover" />
            </Card>

            <Card className="p-8 lg:p-12 border border-gray-200 bg-white flex flex-col">
              <div className="flex items-center gap-3 mb-6">
                <Wand2 className="w-8 h-8" />
                <h3 className="text-2xl lg:text-3xl">AI 시뮬레이션</h3>
              </div>
              <ul className="space-y-3 text-gray-600 flex-grow mb-6">
                {["추천 기반 시뮬레이션","이미지 기반 시뮬레이션","스타일 미리 체험하기","Before / After 비교","AI 스타일 생성"].map((item) => (
                  <li key={item} className="flex items-start gap-2"><span className="mt-1">•</span><span>{item}</span></li>
                ))}
              </ul>
              <img src="https://images.unsplash.com/photo-1595331292515-a6449d5215e9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtaW5pbWFsaXN0JTIwZmFzaGlvbiUyMHBob3RvZ3JhcGh5fGVufDF8fHx8MTc3OTE3NDk5Mnww&ixlib=rb-4.1.0&q=80&w=1080" alt="AI Simulation" className="w-full h-64 object-cover" />
            </Card>
          </div>
        </div>
      </section>

      {/* AI Process Section */}
      <section className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl lg:text-5xl tracking-tight mb-12 text-center">이용 방법</h2>
          <div className="flex justify-center">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-6 max-w-fit">
              {[
                { number: "01", title: "사진 업로드", icon: <Upload className="w-6 h-6" /> },
                { number: "02", title: "AI 분석", icon: <Sparkles className="w-6 h-6" /> },
                { number: "03", title: "추천 결과 확인", icon: <Palette className="w-6 h-6" /> },
                { number: "04", title: "추천 선택 또는 이미지 업로드", icon: <ImagePlay className="w-6 h-6" /> },
                { number: "05", title: "AI 시뮬레이션 생성", icon: <Wand2 className="w-6 h-6" /> },
                { number: "06", title: "AI 챗봇 상담", icon: <MessageSquare className="w-6 h-6" /> },
                { number: "07", title: "결과 저장", icon: <Save className="w-6 h-6" /> },
              ].map((step) => (
                <div key={step.number} className="space-y-4">
                  <div className="flex items-center gap-3">
                    {step.icon}
                    <span className="text-3xl text-gray-300">{step.number}</span>
                  </div>
                  <h3 className="text-base leading-tight">{step.title}</h3>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Analysis Elements Section */}
      <section className="bg-gray-50 py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl lg:text-5xl tracking-tight mb-12 text-center">분석 요소</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {[
              { icon: <User className="w-8 h-8" />, label: "얼굴형", description: "얼굴 윤곽과 비율을 분석해 어울리는 헤어 방향을 추천합니다." },
              { icon: <Paintbrush className="w-8 h-8" />, label: "피부톤", description: "피부 색감과 밝기를 분석해 어울리는 메이크업 톤을 제안합니다." },
              { icon: <Palette className="w-8 h-8" />, label: "퍼스널 컬러", description: "피부톤을 기반으로 어울리는 컬러 팔레트를 추천합니다." },
              { icon: <Scissors className="w-8 h-8" />, label: "헤어스타일", description: "얼굴형과 분위기에 맞는 헤어 스타일을 추천합니다." },
              { icon: <Eye className="w-8 h-8" />, label: "메이크업", description: "피부톤과 얼굴 분위기에 맞는 메이크업 스타일을 제안합니다." },
              { icon: <Palette className="w-8 h-8" />, label: "컬러 밸런스", description: "전체 스타일의 색 조합과 톤 균형을 분석합니다." },
              { icon: <Sparkles className="w-8 h-8" />, label: "스타일 무드", description: "현재 코디의 분위기와 스타일 방향을 분석합니다." },
              { icon: <Wand2 className="w-8 h-8" />, label: "AI 시뮬레이션", description: "추천 스타일을 이미지로 미리 확인할 수 있습니다." },
              { icon: <ArrowLeftRight className="w-8 h-8" />, label: "Before / After", description: "원본 사진과 시뮬레이션 결과를 비교합니다." },
              { icon: <ImagePlay className="w-8 h-8" />, label: "추천 선택", description: "추천 카드 중 원하는 스타일을 선택하거나 랜덤으로 조합합니다." },
            ].map((element, idx) => (
              <Card
                key={idx}
                className="group p-6 border border-gray-200 bg-white text-center transition-all duration-300 hover:bg-black hover:border-black cursor-pointer overflow-hidden"
              >
                <div className="flex flex-col items-center gap-3">
                  <div className="transition-colors duration-300 group-hover:text-white">{element.icon}</div>
                  <span className="text-sm transition-colors duration-300 group-hover:text-white">{element.label}</span>
                  <p className="text-xs text-gray-600 max-h-0 opacity-0 group-hover:max-h-24 group-hover:opacity-100 group-hover:text-white transition-all duration-300 overflow-hidden mt-0 group-hover:mt-2">
                    {element.description}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA Section */}
      <section className="py-16 lg:py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
          <div className="text-4xl lg:text-5xl tracking-tight mb-6">StyleFlow</div>
          <h2 className="text-4xl lg:text-5xl tracking-tight mb-12">AI와 함께 나만의 스타일을 찾아보세요</h2>

          <div className="relative overflow-hidden py-8">
            <div className="flex gap-6 animate-scroll">
              {[
                { image: "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=400&h=500&fit=crop", caption: "Soft Layered Hair", category: "헤어 추천" },
                { image: "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=500&fit=crop", caption: "Warm Tone Makeup", category: "메이크업 추천" },
                { image: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=500&fit=crop", caption: "Monochrome Street Look", category: "코디 추천" },
                { image: "https://images.unsplash.com/photo-1619218533116-f050e7d91d91?w=400&h=500&fit=crop", caption: "AI Simulation Preview", category: "Before / After 시뮬레이션" },
                { image: "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400&h=500&fit=crop", caption: "Volume Long Hair", category: "헤어 추천" },
                { image: "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=400&h=500&fit=crop", caption: "Natural Beige Makeup", category: "메이크업 추천" },
                { image: "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&h=500&fit=crop", caption: "Basic Layered Style", category: "코디 추천" },
                { image: "https://images.unsplash.com/photo-1619749623747-c256b910961a?w=400&h=500&fit=crop", caption: "Style Transformation", category: "Before / After 시뮬레이션" },
                { image: "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=400&h=500&fit=crop", caption: "Soft Layered Hair", category: "헤어 추천" },
                { image: "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=500&fit=crop", caption: "Warm Tone Makeup", category: "메이크업 추천" },
                { image: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=500&fit=crop", caption: "Monochrome Street Look", category: "코디 추천" },
                { image: "https://images.unsplash.com/photo-1619218533116-f050e7d91d91?w=400&h=500&fit=crop", caption: "AI Simulation Preview", category: "Before / After 시뮬레이션" },
                { image: "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400&h=500&fit=crop", caption: "Volume Long Hair", category: "헤어 추천" },
                { image: "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=400&h=500&fit=crop", caption: "Natural Beige Makeup", category: "메이크업 추천" },
                { image: "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&h=500&fit=crop", caption: "Basic Layered Style", category: "코디 추천" },
                { image: "https://images.unsplash.com/photo-1619749623747-c256b910961a?w=400&h=500&fit=crop", caption: "Style Transformation", category: "Before / After 시뮬레이션" },
              ].map((item, idx) => (
                <div key={idx} className="flex-shrink-0 w-64 group cursor-pointer transition-transform duration-300 hover:scale-105">
                  <div className="border border-gray-200 bg-white overflow-hidden hover:shadow-lg transition-shadow duration-300">
                    <div className="relative h-80">
                      <img src={item.image} alt={item.caption} className="w-full h-full object-cover" />
                      <div className="absolute top-3 left-3">
                        <span className="text-xs bg-white/90 px-2 py-1 text-black">{item.category}</span>
                      </div>
                    </div>
                    <div className="p-4 bg-white">
                      <p className="text-sm text-gray-900">{item.caption}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Button
            size="lg"
            onClick={() => router.push("/upload")}
            className="bg-black text-white hover:bg-gray-800 text-base px-12 py-6 mt-8"
          >
            스타일 분석 시작하기
          </Button>
        </div>
      </section>
    </div>
  );
}
