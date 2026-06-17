'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import { Pencil, Trash2, Plus } from 'lucide-react';
import api from '@/lib/api';

type HairStyle = { id: number; style_name: string; hair_code: string | null; image_url: string | null };
type MakeupStyle = { id: number; style_name: string; image_url: string | null };

// ── 헤어스타일 ────────────────────────────────────────────────────────────

function HairStyleTab() {
  const [items, setItems] = useState<HairStyle[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<HairStyle | null>(null);
  const [form, setForm] = useState({ style_name: '', hair_code: '', image_url: '' });

  const load = () => api.get('/admin/hair-styles/').then((r) => setItems(r.data.results ?? r.data));

  useEffect(() => { load(); }, []);

  const openAdd = () => {
    setEditing(null);
    setForm({ style_name: '', hair_code: '', image_url: '' });
    setOpen(true);
  };

  const openEdit = (item: HairStyle) => {
    setEditing(item);
    setForm({ style_name: item.style_name, hair_code: item.hair_code ?? '', image_url: item.image_url ?? '' });
    setOpen(true);
  };

  const handleSave = async () => {
    const payload = {
      style_name: form.style_name,
      hair_code: form.hair_code || null,
      image_url: form.image_url || null,
    };
    if (editing) {
      await api.put(`/admin/hair-styles/${editing.id}/`, payload);
    } else {
      await api.post('/admin/hair-styles/', payload);
    }
    setOpen(false);
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('삭제하시겠습니까?')) return;
    await api.delete(`/admin/hair-styles/${id}/`);
    load();
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Button onClick={openAdd} className="bg-black text-white hover:bg-gray-800 gap-1.5">
          <Plus size={16} /> 헤어스타일 추가
        </Button>
      </div>

      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-gray-500">
              <th className="text-left px-4 py-3 font-medium w-12">ID</th>
              <th className="text-left px-4 py-3 font-medium">스타일명</th>
              <th className="text-left px-4 py-3 font-medium w-24">헤어코드</th>
              <th className="text-left px-4 py-3 font-medium">이미지 URL</th>
              <th className="text-left px-4 py-3 font-medium w-20">미리보기</th>
              <th className="px-4 py-3 w-20" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-400">등록된 항목이 없습니다.</td></tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400">{item.id}</td>
                <td className="px-4 py-3 font-medium">{item.style_name}</td>
                <td className="px-4 py-3 text-gray-500">{item.hair_code ?? '-'}</td>
                <td className="px-4 py-3 text-gray-400 max-w-xs truncate">{item.image_url ?? '-'}</td>
                <td className="px-4 py-3">
                  {item.image_url
                    ? <img src={item.image_url} alt={item.style_name} className="w-10 h-10 object-cover rounded" />
                    : <span className="text-gray-300 text-xs">없음</span>
                  }
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => openEdit(item)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-black transition-colors">
                      <Pencil size={14} />
                    </button>
                    <button onClick={() => handleDelete(item.id)} className="p-1.5 rounded hover:bg-red-50 text-gray-500 hover:text-red-600 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? '헤어스타일 수정' : '헤어스타일 추가'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="block text-sm font-medium mb-1.5">스타일명 *</label>
              <Input value={form.style_name} onChange={(e) => setForm({ ...form, style_name: e.target.value })} placeholder="예: 레이어드컷" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">헤어코드</label>
              <Input value={form.hair_code} onChange={(e) => setForm({ ...form, hair_code: e.target.value })} placeholder="예: H001" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">이미지 URL</label>
              <Input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
              {form.image_url && (
                <img src={form.image_url} alt="preview" className="mt-2 w-20 h-20 object-cover rounded border border-gray-200" />
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>취소</Button>
            <Button onClick={handleSave} disabled={!form.style_name} className="bg-black text-white hover:bg-gray-800">
              {editing ? '수정' : '추가'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── 메이크업스타일 ─────────────────────────────────────────────────────────

function MakeupStyleTab() {
  const [items, setItems] = useState<MakeupStyle[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<MakeupStyle | null>(null);
  const [form, setForm] = useState({ style_name: '', image_url: '' });

  const load = () => api.get('/admin/makeup-styles/').then((r) => setItems(r.data.results ?? r.data));

  useEffect(() => { load(); }, []);

  const openAdd = () => {
    setEditing(null);
    setForm({ style_name: '', image_url: '' });
    setOpen(true);
  };

  const openEdit = (item: MakeupStyle) => {
    setEditing(item);
    setForm({ style_name: item.style_name, image_url: item.image_url ?? '' });
    setOpen(true);
  };

  const handleSave = async () => {
    const payload = { style_name: form.style_name, image_url: form.image_url || null };
    if (editing) {
      await api.put(`/admin/makeup-styles/${editing.id}/`, payload);
    } else {
      await api.post('/admin/makeup-styles/', payload);
    }
    setOpen(false);
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('삭제하시겠습니까?')) return;
    await api.delete(`/admin/makeup-styles/${id}/`);
    load();
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Button onClick={openAdd} className="bg-black text-white hover:bg-gray-800 gap-1.5">
          <Plus size={16} /> 메이크업스타일 추가
        </Button>
      </div>

      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-gray-500">
              <th className="text-left px-4 py-3 font-medium w-12">ID</th>
              <th className="text-left px-4 py-3 font-medium">스타일명</th>
              <th className="text-left px-4 py-3 font-medium">이미지 URL</th>
              <th className="text-left px-4 py-3 font-medium w-20">미리보기</th>
              <th className="px-4 py-3 w-20" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-400">등록된 항목이 없습니다.</td></tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400">{item.id}</td>
                <td className="px-4 py-3 font-medium">{item.style_name}</td>
                <td className="px-4 py-3 text-gray-400 max-w-xs truncate">{item.image_url ?? '-'}</td>
                <td className="px-4 py-3">
                  {item.image_url
                    ? <img src={item.image_url} alt={item.style_name} className="w-10 h-10 object-cover rounded" />
                    : <span className="text-gray-300 text-xs">없음</span>
                  }
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => openEdit(item)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-black transition-colors">
                      <Pencil size={14} />
                    </button>
                    <button onClick={() => handleDelete(item.id)} className="p-1.5 rounded hover:bg-red-50 text-gray-500 hover:text-red-600 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? '메이크업스타일 수정' : '메이크업스타일 추가'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="block text-sm font-medium mb-1.5">스타일명 *</label>
              <Input value={form.style_name} onChange={(e) => setForm({ ...form, style_name: e.target.value })} placeholder="예: 내추럴 메이크업" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">이미지 URL</label>
              <Input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
              {form.image_url && (
                <img src={form.image_url} alt="preview" className="mt-2 w-20 h-20 object-cover rounded border border-gray-200" />
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>취소</Button>
            <Button onClick={handleSave} disabled={!form.style_name} className="bg-black text-white hover:bg-gray-800">
              {editing ? '수정' : '추가'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── 페이지 ─────────────────────────────────────────────────────────────────

export default function StylesPage() {
  return (
    <div>
      <h1 className="text-2xl font-medium mb-6">스타일 관리</h1>
      <Tabs defaultValue="hair">
        <TabsList className="mb-6">
          <TabsTrigger value="hair">헤어스타일</TabsTrigger>
          <TabsTrigger value="makeup">메이크업스타일</TabsTrigger>
        </TabsList>
        <TabsContent value="hair"><HairStyleTab /></TabsContent>
        <TabsContent value="makeup"><MakeupStyleTab /></TabsContent>
      </Tabs>
    </div>
  );
}
