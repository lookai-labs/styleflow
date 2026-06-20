"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Check, ChevronRight, MessageCircle } from "lucide-react";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import api from "@/lib/api";

/* ────────────────────────────────────────── */
/*  상수                                       */
/* ────────────────────────────────────────── */
const LOADING_STEPS = [
  "이미지 분석 중",
  "스타일 패턴 학습 중",
  "AI 시뮬레이션 생성 중",
  "결과 최적화 중",
];

type StyleType = "makeup" | "hair" | "outfit";
type Phase = "loading" | "results";

const STEP_LABELS: Record<StyleType, string> = {
  makeup: "메이크업",
  hair: "헤어",
  outfit: "코디",
};

const STYLE_ORDER: StyleType[] = ["makeup", "hair", "outfit"];

type SimulationResult = { id: string; image: string; name: string; description: string };

const FALLBACK_RESULTS: Record<StyleType, SimulationResult[]> = {
  makeup: [
    { id: "m1", image: "/reference/makeup/MS1.png", name: "웜 코랄 메이크업", description: "따뜻하고 생기있는 코랄 톤" },
    { id: "m2", image: "/reference/makeup/MS2.png", name: "소프트 뉴트럴",   description: "자연스러운 베이지 톤" },
    { id: "m3", image: "/reference/makeup/MS3.png", name: "로즈 글로우",     description: "은은한 로즈 톤 글로우" },
  ],
  hair: [
    { id: "h1", image: "/reference/hair/MH1.jpg", name: "헤어스타일 1", description: "" },
    { id: "h2", image: "/reference/hair/MH2.jpg", name: "헤어스타일 2", description: "" },
    { id: "h3", image: "/reference/hair/MH3.jpg", name: "헤어스타일 3", description: "" },
  ],
  outfit: [],
};

/* ────────────────────────────────────────── */
/*  컴포넌트                                   */
/* ────────────────────────────────────────── */
function SimulationFlowInner() {
  const router = useRouter();
  const authorized = useRequireAuth();
  const searchParams = useSearchParams();

  // URL ?styles=makeup,hair 파라미터 파싱 — 없으면 makeup+hair만 진행
  const activeStyles: StyleType[] = (() => {
    const param = searchParams.get("styles");
    if (!param) return ["makeup", "hair"];
    const parsed = param.split(",").filter((s): s is StyleType =>
      (["makeup", "hair", "outfit"] as string[]).includes(s)
    );
    return parsed.length > 0 ? parsed : ["makeup", "hair"];
  })();

  // ai-stylist에서 돌아오는 경우 — return / resumeIdx 파라미터로 상태 복원
  const returnParam = searchParams.get("return");
  const resumeIdxParam = searchParams.get("resumeIdx");
  const initialPhase: Phase =
    returnParam === "back" || returnParam === "apply" ? "results" : "loading";
  const initialStyleIndex =
    resumeIdxParam !== null ? parseInt(resumeIdxParam, 10) : 0;

  const [currentStyleIndex, setCurrentStyleIndex] = useState(initialStyleIndex);
  const [completedStyles, setCompletedStyles] = useState<StyleType[]>([]);

  const [phase, setPhase] = useState<Phase>(initialPhase);
  const [loadingStep, setLoadingStep] = useState(0);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showConfirmCard, setShowConfirmCard] = useState(false);

  const [aiModifiedData, setAiModifiedData] = useState<{
    selectedId: string;
    aiImage: string;
  } | null>(null);

  // 실제 GAN 결과 (스타일별 캐시)
  const [ganResults, setGanResults] = useState<Record<string, SimulationResult[]>>({});
  // 업로드된 얼굴 사진 (Before 표시용)
  const [faceImage, setFaceImage] = useState<string>("");
  // 케이스 3: 메이크업 선택 결과 (헤어 단계의 Before 표시용)
  const [makeupResultImage, setMakeupResultImage] = useState<string>("");
  // 분석 결과 (스타일 이름 매핑용)
  const [analysisResult, setAnalysisResult] = useState<{
    hair_mappings?: Array<{ id: number; style_name: string; style_code?: string; image_url?: string }>;
    makeup_mappings?: Array<{ id: number; style_name: string; style_code?: string; image_url?: string }>;
  } | null>(null);
  // 단계별 확정된 스타일 이름
  const [selectedStyleNames, setSelectedStyleNames] = useState<Partial<Record<StyleType, string>>>({});

  const confirmCardRef = useRef<HTMLDivElement>(null);
  const apiCalledRef = useRef(false);

  const currentStyle = activeStyles[currentStyleIndex];
  const results = ganResults[currentStyle] ?? FALLBACK_RESULTS[currentStyle] ?? [];
  const overallProgress = (currentStyleIndex / activeStyles.length) * 100;

  const getMappingName = (category: StyleType): string => {
    const mappings = category === "hair"
      ? analysisResult?.hair_mappings
      : analysisResult?.makeup_mappings;
    return mappings?.[0]?.style_name ?? "";
  };

  const displayResults = results.map((r) => ({
    ...r,
    name: getMappingName(currentStyle) || r.name,
  }));
  const loadingProgress = (loadingStep / LOADING_STEPS.length) * 100;

  /* ── 마운트 시 localStorage에서 상태 복원 ── */
  useEffect(() => {
    const faceImg = localStorage.getItem("styleflow_face_image");
    if (faceImg) setFaceImage(faceImg);

    const ar = localStorage.getItem("styleflow_analysis_result");
    if (ar) { try { setAnalysisResult(JSON.parse(ar)); } catch {} }

    const makeupImg = localStorage.getItem("styleflow_selected_makeup_image");
    if (makeupImg) setMakeupResultImage(makeupImg);

    // 캐시된 GAN 결과 복원
    const cachedRaw = localStorage.getItem("styleflow_makeup_results");
    if (cachedRaw) {
      try {
        const cached: SimulationResult[] = JSON.parse(cachedRaw);
        setGanResults((prev) => ({ ...prev, makeup: cached }));
        // 결과가 있으면 로딩 단계를 건너뜀
        if (initialPhase === "loading") setPhase("results");
      } catch {}
    }

    // 캐시된 선택 상태 복원
    const cachedId = localStorage.getItem("styleflow_selected_id");
    if (cachedId) {
      setSelectedId(cachedId);
      setShowConfirmCard(true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── ai-stylist에서 "결과 적용하기"로 돌아온 경우: AI 이미지 복원 ── */
  useEffect(() => {
    if (returnParam === "apply") {
      const stored = localStorage.getItem("styleflow_ai_result");
      if (stored) {
        try {
          const data = JSON.parse(stored);
          localStorage.removeItem("styleflow_ai_result");
          setAiModifiedData(data);
          setSelectedId(data.selectedId);
          setShowConfirmCard(true);
          localStorage.setItem("styleflow_selected_id", data.selectedId);
        } catch {}
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── 로딩: 진행 애니메이션 + 실제 GAN API 호출 ── */
  useEffect(() => {
    if (phase !== "loading") return;

    // 이미 결과가 있으면 API 재호출 없이 바로 결과 화면으로
    if (ganResults[currentStyle]?.length) {
      setPhase("results");
      return;
    }

    setLoadingStep(0);
    setLoadingError(null);

    // 1~3단계는 8초 간격으로 진행, 4단계는 API 완료 시에만 표시
    let step = 0;
    const interval = setInterval(() => {
      step += 1;
      setLoadingStep(step);
      if (step >= LOADING_STEPS.length - 1) clearInterval(interval); // 3단계에서 멈춤
    }, 2000);

    // 실제 API 호출 (makeup만 지원, hair는 HairFastGAN 미구현으로 건너뜀)
    if (currentStyle === "makeup") {
      if (apiCalledRef.current) return;
      apiCalledRef.current = true;

      const faceDataUrl = localStorage.getItem("styleflow_face_image");
      if (!faceDataUrl) {
        clearInterval(interval);
        setLoadingError("업로드된 얼굴 사진을 찾을 수 없습니다. 다시 업로드해 주세요.");
        return;
      }

      // dataURL → Blob → File
      const [header, base64] = faceDataUrl.split(",");
      const mime = header.match(/:(.*?);/)?.[1] ?? "image/png";
      const binary = atob(base64);
      const arr = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
      const blob = new Blob([arr], { type: mime });
      const file = new File([blob], "face.png", { type: mime });

      const formData = new FormData();
      formData.append("face_image", file);

      const _arRawMakeup = localStorage.getItem("styleflow_analysis_result");
      const _arMakeup = _arRawMakeup ? JSON.parse(_arRawMakeup) : null;
      const makeupRefs = (_arMakeup?.makeup_mappings ?? [])
        .filter((m: { image_url?: string }) => m.image_url)
        .map((m: { style_name: string; image_url?: string }) => ({ name: m.style_name, url: m.image_url }));
      if (makeupRefs.length > 0) {
        formData.append("reference_images", JSON.stringify(makeupRefs));
      }

      api.post<{ results: { id: string; image: string; name: string }[] }>("/simulate/makeup/", formData)
        .then(({ data }) => {
          clearInterval(interval);
          setLoadingStep(LOADING_STEPS.length);
          const mapped: SimulationResult[] = data.results.map((r) => ({
            id: r.id,
            image: r.image,
            name: r.name,
            description: "",
          }));
          setGanResults((prev) => ({ ...prev, makeup: mapped }));
          localStorage.setItem("styleflow_makeup_results", JSON.stringify(mapped));
          setTimeout(() => {
            setPhase("results");
            setSelectedId(null);
            setShowConfirmCard(false);
          }, 400);
        })
        .catch((err: unknown) => {
          clearInterval(interval);
          console.warn("메이크업 시뮬레이션 실패, fallback 결과로 진행:", err);
          setLoadingStep(LOADING_STEPS.length);
          const fallback = FALLBACK_RESULTS.makeup;
          setGanResults((prev) => ({ ...prev, makeup: fallback }));
          localStorage.setItem("styleflow_makeup_results", JSON.stringify(fallback));
          setTimeout(() => {
            setPhase("results");
            setSelectedId(null);
            setShowConfirmCard(false);
          }, 400);
        });
    } else if (currentStyle === "hair") {
      if (apiCalledRef.current) return;
      apiCalledRef.current = true;

      // 케이스 3: 메이크업 선택 결과 이미지 사용 / 케이스 2: 원본 얼굴 이미지 사용
      const makeupImageUrl = localStorage.getItem("styleflow_selected_makeup_image");

      const getImageFile = (): Promise<File> => {
        if (makeupImageUrl) {
          // dataURL (AI 수정본) 처리
          if (makeupImageUrl.startsWith("data:")) {
            const [hdr, b64] = makeupImageUrl.split(",");
            const mime2 = hdr.match(/:(.*?);/)?.[1] ?? "image/png";
            const bin = atob(b64);
            const a = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
            return Promise.resolve(new File([new Blob([a], { type: mime2 })], "face.png", { type: mime2 }));
          }
          // http URL (GAN 결과) fetch
          return fetch(makeupImageUrl)
            .then((res) => res.blob())
            .then((blob) => new File([blob], "face.png", { type: blob.type || "image/png" }));
        }
        // 원본 얼굴 이미지
        const faceDataUrl = localStorage.getItem("styleflow_face_image");
        if (!faceDataUrl) return Promise.reject(new Error("업로드된 얼굴 사진을 찾을 수 없습니다. 다시 업로드해 주세요."));
        const [hdr, b64] = faceDataUrl.split(",");
        const mime2 = hdr.match(/:(.*?);/)?.[1] ?? "image/png";
        const bin = atob(b64);
        const a = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
        return Promise.resolve(new File([new Blob([a], { type: mime2 })], "face.png", { type: mime2 }));
      };

      getImageFile()
        .then((file) => {
          const formData = new FormData();
          formData.append("face_image", file);

          const _arRawHair = localStorage.getItem("styleflow_analysis_result");
          const _arHair = _arRawHair ? JSON.parse(_arRawHair) : null;
          const hairRefs = (_arHair?.hair_mappings ?? [])
            .filter((m: { image_url?: string }) => m.image_url)
            .map((m: { style_name: string; image_url?: string }) => ({ name: m.style_name, url: m.image_url }));
          if (hairRefs.length > 0) {
            formData.append("reference_images", JSON.stringify(hairRefs));
          }

          return api.post<{ results: { id: string; image: string; name: string }[] }>("/simulate/hair/", formData);
        })
        .then(({ data }) => {
          clearInterval(interval);
          setLoadingStep(LOADING_STEPS.length);
          const mapped: SimulationResult[] = data.results.map((r) => ({
            id: r.id,
            image: r.image,
            name: r.name,
            description: "",
          }));
          setGanResults((prev) => ({ ...prev, hair: mapped }));
          setTimeout(() => {
            setPhase("results");
            setSelectedId(null);
            setShowConfirmCard(false);
          }, 400);
        })
        .catch((err: unknown) => {
          clearInterval(interval);
          console.warn("헤어 시뮬레이션 실패, fallback 결과로 진행:", err);
          setLoadingStep(LOADING_STEPS.length);
          const fallback = FALLBACK_RESULTS.hair;
          setGanResults((prev) => ({ ...prev, hair: fallback }));
          setTimeout(() => {
            setPhase("results");
            setSelectedId(null);
            setShowConfirmCard(false);
          }, 400);
        });
    }

    return () => clearInterval(interval);
  }, [phase, currentStyleIndex]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── 결과 카드 선택 ── */
  const handleSelect = (id: string) => {
    setSelectedId(id);
    setShowConfirmCard(true);
    localStorage.setItem("styleflow_selected_id", id);
    setTimeout(() => {
      confirmCardRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 50);
  };

  /* ── AI 상담하기: 선택 카드 정보 + 전체 스타일 목록을 localStorage에 저장 후 이동 ── */
  const handleConsult = () => {
    const selectedResult = results.find((r) => r.id === selectedId);
    const ar = analysisResult as Record<string, unknown> | null;
    localStorage.setItem(
      "styleflow_consultation",
      JSON.stringify({
        selectedId,
        selectedImage: selectedResult?.image ?? "",
        style: currentStyle,
        allStyles: activeStyles.join(","),
        currentStyleIndex,
        styleName: getMappingName(currentStyle),
        simulationResultId: null,
        hairMappings: ar?.hair_mappings ?? [],
        makeupMappings: ar?.makeup_mappings ?? [],
        faceShape: ar?.face_shape ?? null,
        personalColor: ar?.personal_color ?? null,
        hairSummary: ar?.hair_analysis_summary ?? null,
        makeupSummary: ar?.makeup_analysis_summary ?? null,
      })
    );
    router.push("/ai-stylist");
  };

  /* ── 확정하고 다음 단계로 ── */
  const handleConfirm = () => {
    const next = currentStyleIndex + 1;
    if (next < activeStyles.length) {
      // 케이스 3: 메이크업 선택 결과를 헤어 단계 입력으로 저장
      if (currentStyle === "makeup") {
        const selectedResult = results.find((r) => r.id === selectedId);
        const imageToSave =
          aiModifiedData?.selectedId === selectedId && aiModifiedData?.aiImage
            ? aiModifiedData.aiImage
            : selectedResult?.image ?? "";
        if (imageToSave) {
          localStorage.setItem("styleflow_selected_makeup_image", imageToSave);
          setMakeupResultImage(imageToSave);
        }
      }
      apiCalledRef.current = false; // 다음 스타일 단계를 위해 반드시 초기화
      setSelectedStyleNames((prev) => ({ ...prev, [currentStyle]: getMappingName(currentStyle) }));
      setCompletedStyles((prev) => [...prev, currentStyle]);
      setCurrentStyleIndex(next);
      setPhase("loading");
    } else {
      // 최종 확정: 완료 정보를 localStorage에 저장 후 이동
      const allCompleted = [...completedStyles, currentStyle];
      const selectedResult = results.find((r) => r.id === selectedId);
      const afterImage =
        aiModifiedData?.selectedId === selectedId && aiModifiedData?.aiImage
          ? aiModifiedData.aiImage
          : selectedResult?.image ?? "";
      const finalStyleNames = { ...selectedStyleNames, [currentStyle]: getMappingName(currentStyle) };
      localStorage.setItem(
        "styleflow_final_result",
        JSON.stringify({
          completedStyles: allCompleted,
          afterImage,
          beforeImage: faceImage || localStorage.getItem("styleflow_face_image") || "",
          styleNames: finalStyleNames,
        })
      );
      // 시뮬레이션 진행 캐시 정리
      localStorage.removeItem("styleflow_makeup_results");
      localStorage.removeItem("styleflow_selected_id");
      localStorage.removeItem("styleflow_selected_makeup_image");
      router.push("/simulation-complete");
    }
  };

  /* ────────────────────────────────────────── */
  /*  렌더                                       */
  /* ────────────────────────────────────────── */
  if (!authorized) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* ── 상단 스텝 인디케이터 ── */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            {activeStyles.map((style, idx) => (
              <div key={style} className="flex items-center gap-2">
                <div
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    idx === currentStyleIndex
                      ? "bg-black text-white"
                      : completedStyles.includes(style)
                      ? "bg-gray-200 text-gray-500 line-through"
                      : "bg-gray-100 text-gray-400"
                  }`}
                >
                  {completedStyles.includes(style) && <Check className="w-3.5 h-3.5" />}
                  {STEP_LABELS[style]}
                </div>
                {idx < activeStyles.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-gray-300" />
                )}
              </div>
            ))}
          </div>
          <Progress value={overallProgress} className="h-1" />
        </div>

        {/* ════════════════════════════════════ */}
        {/*  1. 로딩 화면                         */}
        {/* ════════════════════════════════════ */}
        {phase === "loading" && (
          <Card className="p-8 border border-gray-200 bg-white max-w-2xl mx-auto">
            {loadingError ? (
              <div className="text-center space-y-4">
                <p className="text-red-600">{loadingError}</p>
                <Button onClick={() => window.location.href = "/upload"} className="bg-black text-white hover:bg-gray-800">
                  다시 업로드하기
                </Button>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-2xl mb-2">
                    {STEP_LABELS[currentStyle]} 시뮬레이션 생성 중
                  </h2>
                  <p className="text-gray-600">
                    AI가 최적의 시뮬레이션 이미지를 생성하는 중입니다...
                  </p>
                </div>

                <Progress value={loadingProgress} className="h-2" />

                <div className="space-y-3">
                  {LOADING_STEPS.map((step, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-3 transition-colors ${
                        idx < loadingStep ? "text-black" : "text-gray-400"
                      }`}
                    >
                      {idx < loadingStep ? (
                        <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
                      ) : (
                        <div className="w-5 h-5 rounded-full border-2 border-current flex-shrink-0" />
                      )}
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )}

        {/* ════════════════════════════════════ */}
        {/*  2. 시뮬레이션 결과 화면               */}
        {/* ════════════════════════════════════ */}
        {phase === "results" && (
          <div>
            <div className="mb-8">
              <h1 className="text-3xl mb-2">시뮬레이션 결과</h1>
              <p className="text-gray-600">
                AI가 생성한 3가지 {STEP_LABELS[currentStyle]} 시뮬레이션 결과입니다.
                마음에 드는 스타일을 선택하세요.
              </p>
            </div>

            {/* Before / After 비교 레이아웃 */}
            <div className="flex flex-col lg:flex-row gap-0 mb-8">

              {/* ── Before 영역 ── */}
              {(() => {
                const isHairAfterMakeup = currentStyle === "hair" && !!makeupResultImage;
                const beforeSrc   = isHairAfterMakeup ? makeupResultImage : (faceImage || "/placeholder-face.png");
                const beforeLabel = isHairAfterMakeup ? "메이크업 적용 사진" : "업로드된 원본 사진";
                return (
                  <div className="flex flex-col lg:w-64 flex-shrink-0">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-semibold tracking-widest text-gray-400 uppercase">Before</span>
                      <span className="text-xs text-gray-400">원본 사진</span>
                    </div>
                    <Card className="overflow-hidden border-2 border-gray-300 h-full">
                      <div className="relative">
                        <img
                          src={beforeSrc}
                          alt="원본"
                          className="w-full h-64 object-cover"
                        />
                      </div>
                      <div className="p-4 bg-gray-50">
                        <p className="text-sm text-gray-500">{beforeLabel}</p>
                      </div>
                    </Card>
                  </div>
                );
              })()}

              {/* ── 구분 화살표 ── */}
              <div className="flex lg:flex-col items-center justify-center px-4 py-6 lg:py-0 gap-1 flex-shrink-0">
                <div className="hidden lg:block w-px flex-1 bg-gray-200" />
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-black text-white flex-shrink-0">
                  <ChevronRight className="w-4 h-4" />
                </div>
                <div className="hidden lg:block w-px flex-1 bg-gray-200" />
                {/* 모바일: 가로 구분선 */}
                <div className="lg:hidden flex-1 h-px bg-gray-200" />
                <div className="lg:hidden flex-1 h-px bg-gray-200" />
              </div>

              {/* ── After 영역 ── */}
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs font-semibold tracking-widest text-black uppercase">After</span>
                  <span className="text-xs text-gray-400">AI 시뮬레이션 결과 — 마음에 드는 스타일을 선택하세요</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 flex-1">
                  {displayResults.map((result) => {
                    const isSelected = selectedId === result.id;
                    const isAiModified = aiModifiedData?.selectedId === result.id;
                    const displayImage =
                      isAiModified && aiModifiedData?.aiImage
                        ? aiModifiedData.aiImage
                        : result.image;
                    return (
                      <Card
                        key={result.id}
                        onClick={() => handleSelect(result.id)}
                        className={`overflow-hidden cursor-pointer transition-all duration-200 border-2 ${
                          isSelected
                            ? "border-black shadow-lg"
                            : "border-gray-200 hover:border-gray-400 hover:shadow-md"
                        }`}
                      >
                        <div className="relative">
                          <img
                            src={displayImage}
                            alt={result.name}
                            className="w-full h-64 object-cover"
                          />
                          {isSelected && (
                            <div className="absolute inset-0 bg-black/10 flex items-start justify-end p-3">
                              <div className="bg-black text-white rounded-full w-7 h-7 flex items-center justify-center shadow">
                                <Check className="w-4 h-4" />
                              </div>
                            </div>
                          )}
                          {isAiModified && (
                            <div className="absolute bottom-2 left-2">
                              <Badge className="bg-black text-white text-xs">AI 수정됨</Badge>
                            </div>
                          )}
                        </div>
                        <div className="p-4 flex items-center justify-between">
                          <div>
                            <h3 className="font-medium">{result.name}</h3>
                            <p className="text-sm text-gray-500 mt-0.5">{result.description}</p>
                          </div>
                          {isSelected && (
                            <Badge className="bg-black text-white ml-3 flex-shrink-0">
                              선택됨
                            </Badge>
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>

            </div>

            {/* ── 확인 카드 (선택 즉시 등장) ── */}
            <div
              ref={confirmCardRef}
              className={`transition-all duration-300 overflow-hidden ${
                showConfirmCard ? "max-h-40 opacity-100" : "max-h-0 opacity-0"
              }`}
            >
              <Card className="p-6 border-2 border-black bg-white">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-medium mb-1">
                      이 스타일이 마음에 드시나요?
                    </h3>
                    <p className="text-sm text-gray-500">
                      AI 상담으로 스타일을 더 다듬거나, 바로 다음 단계로 진행할 수 있습니다.
                    </p>
                  </div>
                  <div className="flex gap-3 flex-shrink-0">
                    <Button
                      variant="outline"
                      onClick={handleConsult}
                      className="border-2 border-black whitespace-nowrap"
                    >
                      <MessageCircle className="mr-2 h-4 w-4" />
                      AI 상담하기
                    </Button>
                    <Button
                      onClick={handleConfirm}
                      className="bg-black text-white hover:bg-gray-800 whitespace-nowrap"
                    >
                      확정하고 다음 단계로
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default function SimulationFlowPage() {
  return (
    <Suspense>
      <SimulationFlowInner />
    </Suspense>
  );
}
