"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Check, Home, MessageSquare, RotateCcw, Save } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";

const FALLBACK_BEFORE = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwbW9kZWwlMjBmYWNlJTIwcG9ydHJhaXR8ZW58MXx8fHwxNzc5MTc0OTkxfDA&ixlib=rb-4.1.0&q=80&w=1080";
const FALLBACK_AFTER  = "https://images.unsplash.com/photo-1619218533116-f050e7d91d91?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwZWRpdG9yaWFsJTIwaGFpcnN0eWxlfGVufDF8fHx8MTc3OTE3NDk5Mnww&ixlib=rb-4.1.0&q=80&w=1080";

const STYLE_LABEL: Record<string, string> = {
  makeup: "메이크업",
  hair: "헤어",
  outfit: "코디",
};

type FinalResult = {
  completedStyles: string[];
  afterImage: string;
  beforeImage: string;
};

export default function SimulationCompletePage() {
  const router = useRouter();
  const authorized = useRequireAuth();
  const [finalResult, setFinalResult] = useState<FinalResult | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("styleflow_final_result");
    if (stored) {
      try {
        setFinalResult(JSON.parse(stored));
      } catch {}
    }
  }, []);

  const completedSteps = finalResult?.completedStyles ?? ["makeup", "hair"];
  const beforeImage    = finalResult?.beforeImage ?? FALLBACK_BEFORE;
  const afterImage     = finalResult?.afterImage  ?? FALLBACK_AFTER;

  const handleAIConsult = () => {
    const consultData = {
      selectedId: "simulation-complete",
      selectedImage: afterImage,
      style: completedSteps.join(","),
      allStyles: completedSteps.join(","),
      currentStyleIndex: 0,
    };
    localStorage.setItem("styleflow_consultation", JSON.stringify(consultData));
    router.push("/ai-stylist");
  };

  const handleSave = async () => {
    try {
      const afterFilename = afterImage.split('/').pop() ?? '';
      const faceDataUrl = beforeImage.startsWith('data:')
        ? beforeImage
        : localStorage.getItem('styleflow_face_image') ?? '';

      if (!faceDataUrl || !afterFilename) {
        toast.error('저장에 필요한 이미지가 없습니다.');
        return;
      }

      const [header, base64] = faceDataUrl.split(',');
      const mime = header.match(/:(.*?);/)?.[1] ?? 'image/jpeg';
      const binary = atob(base64);
      const arr = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
      const blob = new Blob([arr], { type: mime });

      const formData = new FormData();
      formData.append('face_image', new File([blob], 'face.jpg', { type: mime }));
      formData.append('after_image_filename', afterFilename);
      if (completedSteps.includes('makeup')) formData.append('makeup_name', '웜 코랄 메이크업');
      if (completedSteps.includes('hair'))   formData.append('hair_name', '레이어드 웨이브');

      await api.post('/simulate/save/', formData);
      toast.success('마이홈에 저장되었습니다');
    } catch {
      toast.error('저장에 실패했습니다. 다시 시도해 주세요.');
    }
  };

  if (!authorized) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl tracking-tight mb-4">스타일 시뮬레이션 완료</h1>
          <p className="text-lg text-gray-600">AI 스타일 시뮬레이션이 완료되었습니다</p>
        </div>

        <Card className="p-8 border border-gray-200 bg-white mb-8">
          <h2 className="text-2xl mb-6">최종 시뮬레이션 결과</h2>
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <p className="text-sm text-gray-500 mb-3 text-center">Before</p>
              <img src={beforeImage} alt="Before simulation" className="w-full h-96 object-cover rounded" />
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-3 text-center">After</p>
              <img src={afterImage} alt="After simulation" className="w-full h-96 object-cover rounded" />
            </div>
          </div>
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg mb-4">적용된 스타일 단계</h3>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              {completedSteps.map((step, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className="flex items-center gap-2 bg-gray-100 px-4 py-2 rounded-full">
                    <Check className="w-4 h-4 text-green-600" />
                    <span className="text-sm">{STYLE_LABEL[step] ?? step}</span>
                  </div>
                  {idx < completedSteps.length - 1 && <span className="text-gray-400">→</span>}
                </div>
              ))}
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Button onClick={handleSave} className="bg-black text-white hover:bg-gray-800 py-6 text-lg">
              <Save className="mr-2 h-5 w-5" />결과 저장
            </Button>
            <Button onClick={() => router.push("/my-home")} className="bg-black text-white hover:bg-gray-800 py-6 text-lg">
              <Home className="mr-2 h-5 w-5" />마이홈으로 이동
            </Button>
          </div>
          <Button
            onClick={handleAIConsult}
            variant="outline"
            className="w-full border-2 border-black py-6 text-lg"
          >
            <MessageSquare className="mr-2 h-5 w-5" />AI 상담하기
          </Button>
          <Button onClick={() => router.push("/result/face")} variant="outline" className="w-full border-2 border-gray-300 py-6 text-lg">
            <RotateCcw className="mr-2 h-5 w-5" />다시 시뮬레이션하기
          </Button>
        </div>

        <Card className="p-6 border border-gray-200 bg-white mt-8">
          <p className="text-sm text-gray-600 text-center">저장된 결과는 마이홈에서 언제든지 확인하고 다시 수정할 수 있습니다.</p>
        </Card>
      </div>
    </div>
  );
}
