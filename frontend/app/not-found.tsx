import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-6">
        <h1 className="text-6xl font-light">404</h1>
        <h2 className="text-2xl">페이지를 찾을 수 없습니다</h2>
        <p className="text-gray-600">요청하신 페이지가 존재하지 않습니다.</p>
        <Link href="/" className="inline-block bg-black text-white px-8 py-3 hover:bg-gray-800 transition-colors">
          홈으로 돌아가기
        </Link>
      </div>
    </div>
  );
}
