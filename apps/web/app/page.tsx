"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

type SegmentReady = { id: string; path: string; durationS: number; host: string };

export default function Home() {
  const [src, setSrc] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

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

  // Ask the API to make a new segment, then poll until THAT segment (same id) is the latest one.
  async function generate() {
    setGenerating(true);
    setStatus("جارٍ توليد مقطع جديد… قد يستغرق نحو دقيقة");
    try {
      const start = await fetch(`${API}/dev/segment/weather`, { method: "POST" });
      if (!start.ok) throw new Error(`HTTP ${start.status}`);
      const { id }: { id: string } = await start.json();

      const deadline = Date.now() + 120_000; // give up after 2 minutes
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 2000));
        const res = await fetch(`${API}/segments/latest`);
        if (!res.ok) continue; // 404 = nothing finished yet, keep waiting
        const seg: SegmentReady = await res.json();
        if (seg.id === id) {
          setStatus("");
          setSrc(`${API}/media/${seg.path}`);
          return;
        }
      }
      setStatus("استغرق التوليد وقتا طويلا، حاول مرة أخرى");
    } catch {
      setStatus("تعذّر الاتصال بالخادم");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-4xl font-bold">إذاعة هواء</h1>
      <div className="flex flex-wrap justify-center gap-3">
        <button
          onClick={generate}
          disabled={loading || generating}
          className="rounded-full bg-foreground px-8 py-3 text-lg text-background disabled:opacity-50"
        >
          {generating ? "جارٍ التوليد…" : "توليد مقطع جديد"}
        </button>
        <button
          onClick={play}
          disabled={loading || generating}
          className="rounded-full border border-foreground px-8 py-3 text-lg disabled:opacity-50"
        >
          {loading ? "جارٍ التحميل…" : "تشغيل آخر مقطع"}
        </button>
      </div>
      {status && <p className="text-start text-zinc-500">{status}</p>}
      {src && <audio key={src} controls autoPlay src={src} className="w-full max-w-md" />}
    </main>
  );
}
