"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

type SegmentReady = { id: string; path: string; durationS: number; host: string };

export default function Home() {
  const [src, setSrc] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);

  async function play() {
    setLoading(true);
    setStatus("");
    try {
      const res = await fetch(`${API}/segments/latest`);
      if (res.status === 404) {
        setStatus("لا توجد مقاطع بعد");
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const seg: SegmentReady = await res.json();
      setSrc(`${API}/media/${seg.path}`);
    } catch {
      setStatus("تعذّر الاتصال بالخادم");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-4xl font-bold">إذاعة هواء</h1>
      <button
        onClick={play}
        disabled={loading}
        className="rounded-full bg-foreground px-8 py-3 text-lg text-background disabled:opacity-50"
      >
        {loading ? "جارٍ التحميل…" : "تشغيل آخر مقطع"}
      </button>
      {status && <p className="text-start text-zinc-500">{status}</p>}
      {src && <audio key={src} controls autoPlay src={src} className="w-full max-w-md" />}
    </main>
  );
}
