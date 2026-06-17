"use client";

import { useState } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Check } from "lucide-react";

interface StylingSelectionModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (selected: { makeup: boolean; hair: boolean }) => void;
  type: "face" | "outfit";
}

export function StylingSelectionModal({ open, onClose, onConfirm, type }: StylingSelectionModalProps) {
  const [selected, setSelected] = useState({ makeup: false, hair: false });

  const handleToggle = (key: "makeup" | "hair") => {
    setSelected((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleConfirm = () => {
    if (!selected.makeup && !selected.hair) return;
    onConfirm(selected);
    onClose();
  };

  const hasSelection = selected.makeup || selected.hair;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl mb-2">시뮬레이션 항목 선택</DialogTitle>
          <DialogDescription className="text-sm text-gray-600">
            시뮬레이션할 스타일 요소를 선택하세요
          </DialogDescription>
        </DialogHeader>

        <div className="grid md:grid-cols-2 gap-4 pt-4">
          {([
            { key: "makeup" as const, title: "메이크업", desc: "피부톤에 맞는 메이크업 스타일" },
            { key: "hair" as const, title: "헤어", desc: "얼굴형에 어울리는 헤어 스타일" },
          ]).map(({ key, title, desc }) => (
            <Card
              key={key}
              onClick={() => handleToggle(key)}
              className={`p-6 cursor-pointer transition-all border-2 ${
                selected[key] ? "border-black bg-black text-white" : "border-gray-200 bg-white hover:border-gray-400"
              }`}
            >
              <div className="flex flex-col items-center gap-4">
                <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center ${selected[key] ? "border-white" : "border-gray-300"}`}>
                  {selected[key] && <Check className="w-6 h-6" />}
                </div>
                <div className="text-center">
                  <h3 className="text-lg mb-1">{title}</h3>
                  <p className={`text-xs ${selected[key] ? "text-white/80" : "text-gray-500"}`}>{desc}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="flex gap-3 pt-6">
          <Button onClick={onClose} variant="outline" className="flex-1 border-2 border-gray-300">취소</Button>
          <Button onClick={handleConfirm} disabled={!hasSelection} className="flex-1 bg-black text-white hover:bg-gray-800 disabled:opacity-50">
            시뮬레이션 시작
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
