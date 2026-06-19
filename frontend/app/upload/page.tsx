"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Upload, Check, Camera, Sun, User, Image as ImageIcon } from "lucide-react";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import api from "@/lib/api";

const analysisSteps = [
  "얼굴 영역 감지 중",
  "얼굴형 분석 중",
  "피부톤 감지 중",
  "헤어스타일 추천 생성 중",
  "메이크업 추천 생성 중",
  "AI 시뮬레이션 준비 중",
];

const FALLBACK_ANALYSIS_RESULT = {
  hair_analysis_summary:
    "RAG 분석 서버 연결이 불안정해 기본 분석 결과로 진행합니다. 둥근형 얼굴에는 이마와 옆선을 정돈해 세로감을 보완하는 스타일을 우선 추천합니다.",
  makeup_analysis_summary:
    "RAG 분석 서버 연결이 불안정해 기본 분석 결과로 진행합니다. 봄웜 톤에는 코랄, 피치, 내추럴 계열 메이크업을 우선 추천합니다.",
  face_shape: "둥근형",
  skin_tone: "spring",
  personal_color: "봄웜",
  hair_mappings: [
    { id: 0, style_name: "아이비리그", style_code: "m-03", image_url: "" },
    { id: 1, style_name: "댄디", style_code: "m-08", image_url: "" },
    { id: 2, style_name: "애즈", style_code: "m-12", image_url: "" },
  ],
  makeup_mappings: [
    { id: 0, style_name: "코랄 메이크업", style_code: "mk-sp-coral", image_url: "" },
    { id: 1, style_name: "피치 메이크업", style_code: "mk-sp-peach", image_url: "" },
    { id: 2, style_name: "봄웜 내추럴 메이크업", style_code: "mk-m-sp-natural", image_url: "" },
  ],
};

function UploadPageInner() {
  const router = useRouter();
  const authorized = useRequireAuth();
  const searchParams = useSearchParams();
  const type = (searchParams.get("type") ?? "face") as "face" | "outfit";

  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  // 인터벌 ref — 언마운트 시 cleanup
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    window.scrollTo(0, 0);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const compressImage = (dataUrl: string): Promise<string> =>
    new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const MAX = 800;
        const ratio = Math.min(MAX / img.width, MAX / img.height, 1);
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.width * ratio);
        canvas.height = Math.round(img.height * ratio);
        canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.8));
      };
      img.src = dataUrl;
    });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      const reader = new FileReader();
      reader.onloadend = async () => {
        const dataUrl = reader.result as string;
        setUploadedImage(dataUrl);
        const compressed = await compressImage(dataUrl);
        localStorage.setItem("styleflow_face_image", compressed);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalysis = async () => {
    window.scrollTo({ top: 0, behavior: "smooth" });

    setTimeout(async () => {
      setIsAnalyzing(true);

      // API 호출과 애니메이션을 병렬 실행, 둘 다 끝나면 이동
      const formData = new FormData();
      formData.append("face_shape", "round");
      formData.append("face_point", "golden");
      formData.append("skin_tone", "spring");

      if (uploadedFile) {
        formData.append("face_image", uploadedFile);
      } else {
        const faceDataUrl = localStorage.getItem("styleflow_face_image");
        if (faceDataUrl) {
          const [header, base64] = faceDataUrl.split(",");
          const mime = header.match(/:(.*?);/)?.[1] ?? "image/jpeg";
          const binary = atob(base64);
          const arr = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
          const blob = new Blob([arr], { type: mime });
          formData.append("face_image", new File([blob], "face.jpg", { type: mime }));
        }
      }

      const apiCall = api.post("/analyze/", formData)
        .then((res) => {
          localStorage.setItem("styleflow_analysis_result", JSON.stringify(res.data));
        })
        .catch((e) => {
          console.warn("RAG 분석 실패, 더미 데이터로 진행:", e);
          localStorage.setItem("styleflow_analysis_result", JSON.stringify(FALLBACK_ANALYSIS_RESULT));
        });

      const animation = new Promise<void>((resolve) => {
        let step = 0;
        intervalRef.current = setInterval(() => {
          step++;
          setCurrentStep(step);
          if (step >= analysisSteps.length) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = null;
            resolve();
          }
        }, 800);
      });

      try {
        await Promise.all([apiCall, animation]);
      } catch (e) {
        console.warn("분석 처리 중 예외가 발생해 fallback 결과로 진행합니다:", e);
        localStorage.setItem("styleflow_analysis_result", JSON.stringify(FALLBACK_ANALYSIS_RESULT));
      } finally {
        setTimeout(() => {
          router.push(`/result/${type}`);
        }, 500);
      }
    }, 300);
  };

  const progress = (currentStep / analysisSteps.length) * 100;

  if (!authorized) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl tracking-tight mb-4">AI 스타일 분석 시작하기</h1>
          <p className="text-lg text-gray-600">사진을 업로드하여 AI 기반 스타일 분석을 받아보세요.</p>
        </div>

        {!isAnalyzing ? (
          <div className="space-y-8">
            <Card className="p-8 border border-gray-200 bg-white">
              <div className="grid md:grid-cols-4 gap-6">
                {[
                  { icon: <Camera className="w-6 h-6 text-gray-600" />, title: "정면 사진 사용", desc: "얼굴이 정면을 향한 사진" },
                  { icon: <Sun className="w-6 h-6 text-gray-600" />, title: "밝은 조명 권장", desc: "자연광 또는 밝은 실내" },
                  { icon: <User className="w-6 h-6 text-gray-600" />, title: "얼굴 가리지 않기", desc: "명확한 얼굴 가시성" },
                  { icon: <ImageIcon className="w-6 h-6 text-gray-600" />, title: "흐릿한 사진 지양", desc: "선명한 고해상도 이미지" },
                ].map((guide) => (
                  <div key={guide.title} className="flex flex-col items-center text-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                      {guide.icon}
                    </div>
                    <div>
                      <p className="font-medium text-sm mb-1">{guide.title}</p>
                      <p className="text-xs text-gray-500">{guide.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div>
              {!uploadedImage ? (
                <Card className="border-2 border-dashed border-gray-300 bg-white">
                  <label className="flex flex-col items-center justify-center py-16 cursor-pointer hover:bg-gray-50 transition-colors">
                    <Upload className="w-12 h-12 text-gray-400 mb-4" />
                    <p className="text-lg mb-2">사진을 업로드하거나 클릭하여 찾아보기</p>
                    <p className="text-sm text-gray-500">PNG, JPG 최대 10MB</p>
                    <input type="file" className="hidden" accept="image/*" onChange={handleFileUpload} />
                  </label>
                </Card>
              ) : (
                <div className="space-y-4">
                  <Card className="p-4 border border-gray-200 bg-white">
                    <img src={uploadedImage} alt="Uploaded" className="w-full max-h-96 object-contain" />
                  </Card>
                  <div className="flex gap-4">
                    <Button variant="outline" onClick={() => setUploadedImage(null)} className="border-2 border-black">
                      사진 변경
                    </Button>
                    <Button onClick={handleAnalysis} className="flex-1 bg-black text-white hover:bg-gray-800">
                      AI 분석 시작
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <Card className="p-8 border border-gray-200 bg-white">
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl mb-2">스타일 분석 중</h2>
                <p className="text-gray-600">AI가 사진을 분석하는 동안 잠시만 기다려 주세요...</p>
              </div>
              <Progress value={progress} className="h-2" />
              <div className="space-y-3">
                {analysisSteps.map((step, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 ${idx <= currentStep ? "text-black" : "text-gray-400"}`}
                  >
                    {idx < currentStep ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-current" />
                    )}
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function AnalysisUploadPage() {
  return (
    <Suspense>
      <UploadPageInner />
    </Suspense>
  );
}
