"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Send, ArrowLeft, Check } from "lucide-react";
import axios from "axios";

/* ── 타입 ── */
type Message = {
  role: "assistant" | "user";
  content?: string;   // 텍스트 (없으면 이미지만)
  image?: string;     // 이미지 URL (없으면 텍스트만)
};

type ConsultData = {
  selectedId: string;
  selectedImage: string;
  style: string;
  allStyles: string;        // "makeup,hair" 형식
  currentStyleIndex: number;
};

/* ── 더미 데이터 ── */
const AI_IMAGES = [
  "https://images.unsplash.com/photo-1596704017254-9b121068fb31?w=800",
  "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=800",
  "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=800",
  "https://images.unsplash.com/photo-1522337660859-02fbefca4702?w=800",
  "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800",
];

const AI_TEXTS = [
  "요청하신 방향으로 스타일을 수정했어요.",
  "말씀해주신 내용을 반영해 새로운 시뮬레이션을 생성했습니다.",
  "웜톤 피부에 잘 어울리는 새로운 스타일을 제안드립니다.",
  "분석 결과를 바탕으로 맞춤 스타일 이미지를 생성했어요. 마음에 드시나요?",
  "수정된 스타일 이미지가 준비됐습니다. 추가 조정이 필요하면 말씀해주세요.",
];

let imgCursor = 0;
let txtCursor = 0;

/* ── 말풍선 컴포넌트 ── */
function Bubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";

  // 이미지만 있는 경우: 배경 없이 이미지 그대로 표시
  if (msg.image && !msg.content) {
    return (
      <img
        src={msg.image}
        alt="이미지"
        className="w-48 rounded-lg"
      />
    );
  }

  // 텍스트만 or 텍스트+이미지 (텍스트+이미지는 발생하지 않도록 분리 전송함)
  return (
    <div
      className={`max-w-[75%] p-4 rounded-lg ${
        isUser ? "bg-black text-white" : "bg-gray-100 text-black"
      }`}
    >
      {msg.content && <p>{msg.content}</p>}
      {msg.image && (
        <img src={msg.image} alt="이미지" className="w-full rounded-lg mt-3" />
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

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  // 초기 로딩 메시지 개수 — 이 수 이하면 맨 위로, 초과하면 맨 아래로 스크롤
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
          // 초기 메시지: 이미지(1) + AI 인사(2)
          initialMsgCount.current = 2;
          setMessages([{ role: "user", image: data.selectedImage }]);
          timer = setTimeout(() => {
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content:
                  "분석 결과를 바탕으로 맞춤형 스타일링 추천을 도와드리겠습니다.",
              },
            ]);
          }, 600);
        } else {
          // 초기 메시지: AI 인사(1)만
          initialMsgCount.current = 1;
          setMessages([
            {
              role: "assistant",
              content:
                "분석 결과를 바탕으로 맞춤형 스타일링 추천을 도와드리겠습니다.",
            },
          ]);
        }
      } catch {}
    } else {
      initialMsgCount.current = 1;
      setMessages([
        {
          role: "assistant",
          content:
            "분석 결과를 바탕으로 맞춤형 스타일링 추천을 도와드리겠습니다.",
        },
      ]);
    }

    // StrictMode 두 번 실행 시 첫 번째 타이머를 정리해 메시지 중복 방지
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, []);

  /* ── 스크롤 제어
       초기 메시지(이미지 + AI 인사) 로딩 중 → 페이지 + 컨테이너 맨 위로
       그 이후 사용자/AI 메시지 추가 시  → 컨테이너 맨 아래로 따라가기 ── */
  useEffect(() => {
    if (messages.length === 0) return;

    if (messages.length <= initialMsgCount.current) {
      // 초기 메시지 로딩 단계 — 전체 페이지와 내부 컨테이너 모두 맨 위로
      window.scrollTo({ top: 0, behavior: "smooth" });
      messagesContainerRef.current?.scrollTo({ top: 0 });
    } else {
      // 채팅 진행 중 — 내부 컨테이너를 최신 메시지까지 스크롤
      const container = messagesContainerRef.current;
      if (container) {
        container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
      }
    }
  }, [messages]);

  /* ── 메시지 전송: AI가 텍스트 말풍선 → 이미지 말풍선 순으로 응답 ── */
  const handleSend = async (content: string) => {
    if (!content.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInputValue("");

    const aiImage = AI_IMAGES[imgCursor % AI_IMAGES.length];
    imgCursor++;
    let replyText = AI_TEXTS[txtCursor % AI_TEXTS.length];
    txtCursor++;

    try {
      const res = await axios.post("http://localhost:8000/api/ai-chat/", {
        message: content,
      });
      replyText = res.data.reply;
    } catch {
      /* 백엔드 없으면 더미 텍스트 사용 */
    }

    // ① 텍스트 말풍선 먼저
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: replyText },
      ]);

      // ② 이미지 말풍선 별도로
      setTimeout(() => {
        setMessages((prev) => [...prev, { role: "assistant", image: aiImage }]);
        setLatestAiImage(aiImage);
      }, 400);
    }, 800);
  };

  /* ── 돌아가기 ──
     simulation-flow에서 진입: 전체 스타일 목록 복원하여 시뮬레이션 결과로
     simulation-complete("코디 바꾸기")에서 진입: 시뮬레이션 완료 화면으로 ── */
  const handleGoBack = () => {
    if (!consultData) {
      router.push("/simulation-complete");
      return;
    }
    const allStyles = consultData.allStyles ?? consultData.style ?? "makeup";
    const idx = consultData.currentStyleIndex ?? 0;
    router.push(
      `/simulation-flow?styles=${allStyles}&return=back&resumeIdx=${idx}`
    );
  };

  /* ── 결과 적용하기 ──
     simulation-flow에서 진입: AI 이미지 저장 후 시뮬레이션 결과로
     simulation-complete("코디 바꾸기")에서 진입: 시뮬레이션 완료 화면으로 ── */
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
    router.push(
      `/simulation-flow?styles=${allStyles}&return=apply&resumeIdx=${idx}`
    );
  };

  /* 사이드바 이미지: AI 수정본 > 선택 이미지 > 기본 이미지 */
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
              {/* 메시지 목록: 내용이 늘어나면 카드도 커지고, max-h 이후엔 내부 스크롤 */}
              <div ref={messagesContainerRef} className="overflow-y-auto p-6 space-y-4 min-h-[260px] max-h-[65vh]">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <Bubble msg={msg} />
                  </div>
                ))}
              </div>

              {/* 입력 + 버튼: 카드가 늘어나도 항상 하단에 고정 */}
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
