"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Send, ArrowLeft, Check } from "lucide-react";
import api from "@/lib/api";

/* ── 타입 ── */
type SelectionOption = {
  id: string;
  label: string;
  value?: string;
};

type Selection = {
  type: string;
  title?: string;
  options: SelectionOption[];
};

type Message = {
  role: "assistant" | "user";
  content?: string;
  image?: string;
  selection?: Selection;
};

type ConsultData = {
  selectedId: string;
  selectedImage: string;
  style: string;
  allStyles: string;
  currentStyleIndex: number;
};

type ApiResponse = {
  reply: string;
  updated_chat_history: { role: string; content: string }[];
  updated_user_profile: Record<string, unknown>;
  selection?: Selection | null;
  pending_selection?: string | null;
};

/* ── API 실패 시 폴백 텍스트 ── */
const FALLBACK_TEXTS = [
  "요청하신 방향으로 스타일을 안내해 드릴게요.",
  "말씀해주신 내용을 참고해 새로운 스타일을 제안드립니다.",
  "웜톤 피부에 잘 어울리는 스타일을 제안드립니다.",
];
let fallbackCursor = 0;

/* ── 말풍선 컴포넌트 ── */
function Bubble({
  msg,
  onSelectOption,
}: {
  msg: Message;
  onSelectOption?: (selection: Selection, option: SelectionOption) => void;
}) {
  const isUser = msg.role === "user";

  if (msg.image && !msg.content && !msg.selection) {
    return <img src={msg.image} alt="이미지" className="w-48 rounded-lg" />;
  }

  return (
    <div
      className={`max-w-[75%] p-4 rounded-lg ${
        isUser ? "bg-black text-white" : "bg-gray-100 text-black"
      }`}
    >
      {msg.content && <p className="whitespace-pre-line">{msg.content}</p>}
      {msg.image && (
        <img src={msg.image} alt="이미지" className="w-full rounded-lg mt-3" />
      )}
      {msg.selection && (
        <div className="mt-3 space-y-2">
          {msg.selection.title && (
            <p className="text-sm font-medium mb-2">{msg.selection.title}</p>
          )}
          <div className="flex flex-wrap gap-2">
            {msg.selection.options.map((opt) => (
              <button
                key={opt.id}
                onClick={() => onSelectOption?.(msg.selection!, opt)}
                className="px-3 py-1.5 text-sm border border-gray-400 rounded-full bg-white hover:bg-gray-50 text-black transition-colors"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── 메인 컴포넌트 ── */
export default function AIStylistPage() {
  const router = useRouter();

  const [consultData, setConsultData] = useState<ConsultData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [latestAiImage, setLatestAiImage] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [userProfile, setUserProfile] = useState<Record<string, unknown>>({});

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const initialMsgCount = useRef(0);

  /* ── localStorage에서 상담 데이터 로드 + 초기 메시지 설정 ── */
  useEffect(() => {
    const stored = localStorage.getItem("styleflow_consultation");
    let timer: ReturnType<typeof setTimeout> | null = null;

    if (stored) {
      try {
        const data: ConsultData = JSON.parse(stored);
        setConsultData(data);

        if (data.selectedImage) {
          initialMsgCount.current = 2;
          setMessages([{ role: "user", image: data.selectedImage }]);
          timer = setTimeout(() => {
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: "분석 결과를 바탕으로 맞춤형 스타일링 추천을 도와드리겠습니다.",
              },
            ]);
          }, 600);
        } else {
          initialMsgCount.current = 1;
          setMessages([
            {
              role: "assistant",
              content: "분석 결과를 바탕으로 맞춤형 스타일링 추천을 도와드리겠습니다.",
            },
          ]);
        }
      } catch {}
    } else {
      initialMsgCount.current = 1;
      setMessages([
        {
          role: "assistant",
          content: "분석 결과를 바탕으로 맞춤형 스타일링 추천을 도와드리겠습니다.",
        },
      ]);
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, []);

  /* ── 스크롤 제어 ── */
  useEffect(() => {
    if (messages.length === 0) return;
    if (messages.length <= initialMsgCount.current) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      messagesContainerRef.current?.scrollTo({ top: 0 });
    } else {
      const container = messagesContainerRef.current;
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
      }
    }
  }, [messages]);

  /* ── 백엔드 호출 공통 함수 ── */
  const callChatApi = async (
    message: string,
    selectedOption?: { type: string; id: string }
  ): Promise<ApiResponse> => {
    const analysisRaw = localStorage.getItem("styleflow_analysis_result");
    const analysisResult = analysisRaw ? JSON.parse(analysisRaw) : null;

    const previousAnalysis = analysisResult
      ? [analysisResult.hair_analysis_summary, analysisResult.makeup_analysis_summary]
          .filter(Boolean)
          .join("\n")
      : null;

    const res = await api.post("/ai-chat/", {
      message,
      face_shape: analysisResult?.face_shape ?? "round",
      personal_color: analysisResult?.personal_color ?? "봄 웜톤",
      previous_analysis: previousAnalysis,
      chat_history: chatHistory,
      user_profile: userProfile,
      ...(selectedOption ? { selected_option: selectedOption } : {}),
    });

    return res.data as ApiResponse;
  };

  /* ── API 응답을 채팅창에 반영 ── */
  const applyApiResponse = (data: ApiResponse) => {
    setChatHistory(data.updated_chat_history ?? []);
    setUserProfile(data.updated_user_profile ?? {});

    setTimeout(() => {
      const hasSelection = !!data.selection?.options?.length;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          ...(hasSelection ? { selection: data.selection! } : {}),
        },
      ]);
    }, 800);
  };

  /* ── 메시지 전송 ── */
  const handleSend = async (content: string) => {
    if (!content.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInputValue("");

    try {
      const data = await callChatApi(content);
      applyApiResponse(data);
    } catch {
      const fallback = FALLBACK_TEXTS[fallbackCursor % FALLBACK_TEXTS.length];
      fallbackCursor++;
      setTimeout(() => {
        setMessages((prev) => [...prev, { role: "assistant", content: fallback }]);
      }, 800);
    }
  };

  /* ── 선택 버튼 클릭 처리 ── */
  const handleSelectOption = async (selection: Selection, option: SelectionOption) => {
    setMessages((prev) => [...prev, { role: "user", content: option.label }]);

    try {
      const data = await callChatApi(option.label, {
        type: selection.type,
        id: option.id,
      });
      applyApiResponse(data);
    } catch {
      const fallback = FALLBACK_TEXTS[fallbackCursor % FALLBACK_TEXTS.length];
      fallbackCursor++;
      setTimeout(() => {
        setMessages((prev) => [...prev, { role: "assistant", content: fallback }]);
      }, 800);
    }
  };

  /* ── 돌아가기 ── */
  const handleGoBack = () => {
    if (!consultData) {
      router.push("/simulation-complete");
      return;
    }
    const allStyles = consultData.allStyles ?? consultData.style ?? "makeup";
    const idx = consultData.currentStyleIndex ?? 0;
    router.push(`/simulation-flow?styles=${allStyles}&return=back&resumeIdx=${idx}`);
  };

  /* ── 결과 적용하기 ── */
  const handleApply = () => {
    if (!consultData) {
      router.push("/simulation-complete");
      return;
    }
    if (latestAiImage) {
      localStorage.setItem(
        "styleflow_ai_result",
        JSON.stringify({
          selectedId: consultData.selectedId,
          aiImage: latestAiImage,
        })
      );
    }
    const allStyles = consultData.allStyles ?? consultData.style ?? "makeup";
    const idx = consultData.currentStyleIndex ?? 0;
    router.push(`/simulation-flow?styles=${allStyles}&return=apply&resumeIdx=${idx}`);
  };

  const sidebarImage =
    latestAiImage ??
    consultData?.selectedImage ??
    "https://images.unsplash.com/photo-1619218533116-f050e7d91d91?w=400";

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl lg:text-5xl tracking-tight">
            StyleFlow AI Stylist
          </h1>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* ── 왼쪽 패널 ── */}
          <div className="lg:col-span-1">
            <Card className="p-6 border border-gray-200 bg-white sticky top-24">
              <h3 className="text-lg mb-4">시뮬레이션 결과</h3>
              <div className="space-y-4">
                <Badge className="bg-black text-white">AI 스타일 상담</Badge>
                <div className="space-y-2 text-sm">
                  <div>
                    <p className="text-gray-500">얼굴형</p>
                    <p>부드럽고 둥근형</p>
                  </div>
                  <div>
                    <p className="text-gray-500">피부톤</p>
                    <p>웜톤</p>
                  </div>
                  <div>
                    <p className="text-gray-500">추천 컬러</p>
                    <p>코랄, 베이지, 웜 브라운</p>
                  </div>
                </div>
                <div className="pt-2">
                  <div className="relative">
                    <img
                      src={sidebarImage}
                      alt="시뮬레이션 이미지"
                      className="w-full rounded border border-gray-200"
                    />
                    {latestAiImage && (
                      <div className="absolute bottom-2 left-2">
                        <Badge className="bg-black text-white text-xs">
                          AI 수정됨
                        </Badge>
                      </div>
                    )}
                  </div>
                  {latestAiImage && (
                    <p className="text-xs text-gray-400 mt-1 text-center">
                      AI가 수정한 최신 이미지
                    </p>
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* ── 채팅 영역 ── */}
          <div className="lg:col-span-3">
            <Card className="border border-gray-200 bg-white flex flex-col">
              <div
                ref={messagesContainerRef}
                className="overflow-y-auto p-6 space-y-4 min-h-[260px] max-h-[65vh]"
              >
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <Bubble msg={msg} onSelectOption={handleSelectOption} />
                  </div>
                ))}
              </div>

              <div className="border-t border-gray-200 p-6 flex-shrink-0">
                <div className="flex gap-2 mb-4">
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend(inputValue);
                      }
                    }}
                    placeholder="원하는 스타일 변경을 입력하세요..."
                    className="flex-1"
                  />
                  <Button
                    onClick={() => handleSend(inputValue)}
                    className="bg-black text-white hover:bg-gray-800"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={handleGoBack}
                    className="flex-1 border-2 border-gray-300"
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    돌아가기
                  </Button>
                  <Button
                    onClick={handleApply}
                    disabled={!latestAiImage}
                    className="flex-1 bg-black text-white hover:bg-gray-800 disabled:opacity-40"
                  >
                    <Check className="mr-2 h-4 w-4" />
                    결과 적용하기
                  </Button>
                </div>
                {!latestAiImage && (
                  <p className="text-xs text-gray-400 text-center mt-2">
                    채팅으로 스타일을 요청하면 AI 이미지가 생성됩니다
                  </p>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
