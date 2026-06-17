import Link from "next/link";
import { Share2, Mail, Clock, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-16 lg:py-20">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-8">
            <div className="lg:col-span-1 space-y-6">
              <div>
                <h3 className="text-2xl tracking-tight mb-3">StyleFlow</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  AI 기반 스타일 추천과 시뮬레이션으로<br />
                  나만의 스타일을 경험해보세요.
                </p>
              </div>
              <div className="flex gap-4">
                <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-black transition-colors" aria-label="Instagram">
                  <ExternalLink className="w-5 h-5" />
                </a>
                <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-black transition-colors" aria-label="YouTube">
                  <ExternalLink className="w-5 h-5" />
                </a>
                <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-black transition-colors" aria-label="Pinterest">
                  <Share2 className="w-5 h-5" />
                </a>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-8 lg:col-span-2">
              <div>
                <h4 className="text-sm mb-4 tracking-wide">서비스</h4>
                <ul className="space-y-3">
                  <li><Link href="/upload?type=face" className="text-sm text-gray-600 hover:text-black transition-colors">헤어 &amp; 메이크업 추천</Link></li>
                  <li><Link href="/upload?type=outfit" className="text-sm text-gray-600 hover:text-black transition-colors">코디 추천</Link></li>
                  <li><Link href="/simulation" className="text-sm text-gray-600 hover:text-black transition-colors">AI 시뮬레이션</Link></li>
                  <li><Link href="/my-home" className="text-sm text-gray-600 hover:text-black transition-colors">마이홈</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm mb-4 tracking-wide">AI 기능</h4>
                <ul className="space-y-3">
                  <li className="text-sm text-gray-600">얼굴형 분석</li>
                  <li className="text-sm text-gray-600">피부톤 분석</li>
                  <li className="text-sm text-gray-600">퍼스널 컬러</li>
                  <li className="text-sm text-gray-600">스타일 추천</li>
                  <li className="text-sm text-gray-600">Before / After</li>
                </ul>
              </div>
            </div>

            <div className="lg:col-span-1">
              <h4 className="text-sm mb-4 tracking-wide">Customer</h4>
              <ul className="space-y-3 mb-6">
                <li><Link href="/support" className="text-sm text-gray-600 hover:text-black transition-colors">고객센터</Link></li>
                <li><Link href="/guide" className="text-sm text-gray-600 hover:text-black transition-colors">이용가이드</Link></li>
                <li><Link href="/faq" className="text-sm text-gray-600 hover:text-black transition-colors">FAQ</Link></li>
                <li><Link href="/contact" className="text-sm text-gray-600 hover:text-black transition-colors">문의하기</Link></li>
              </ul>
              <div className="space-y-2 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Mail className="w-4 h-4" />
                  <span>support@styleflow.ai</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Clock className="w-4 h-4" />
                  <span>MON–FRI 10:00–18:00</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-200 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-gray-500">© 2026 StyleFlow. All rights reserved.</p>
            <div className="flex gap-6">
              <Link href="/privacy" className="text-xs text-gray-500 hover:text-black transition-colors">개인정보처리방침</Link>
              <Link href="/terms" className="text-xs text-gray-500 hover:text-black transition-colors">이용약관</Link>
              <Link href="/ai-guide" className="text-xs text-gray-500 hover:text-black transition-colors">AI 생성 가이드</Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
