import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  const [q, setQ] = useState('What is momentum?');
  const [out, setOut] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function invoke() {
    setBusy(true); setErr(null);
    try {
      const r = await fetch('/invoke', {
        method: 'POST',
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ user_id: 'demo', input: { question: q }, context: {} })
      });
      if (!r.ok) throw new Error(await r.text());
      setOut(await r.json());
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{fontFamily:'system-ui', padding:16, maxWidth:800, margin:'0 auto'}}>
      <h2>🎓 TutorAgent</h2>
      <p style={{color:'#555'}}>Standalone UI served by the agent (also embeddable in GENIUS).</p>

      <div style={{display:'flex', gap:8}}>
        <input value={q} onChange={e=>setQ(e.target.value)} style={{flex:1, padding:8, border:'1px solid #ccc', borderRadius:6}} />
        <button onClick={invoke} disabled={busy} style={{padding:'8px 12px', borderRadius:6, background:'#111', color:'#fff'}}>
          {busy ? 'Running…' : 'Invoke'}
        </button>
      </div>

      {err && <div style={{marginTop:12, color:'#a00'}}>Error: {err}</div>}
      <pre style={{background:'#f6f6f6', marginTop:12, padding:12, borderRadius:8, whiteSpace:'pre-wrap'}}>
        {out ? JSON.stringify(out, null, 2) : '← Run an invocation to see output'}
      </pre>

      <div style={{marginTop:16, fontSize:12, color:'#666'}}>
        <a href="/healthz" target="_blank" rel="noreferrer">Health</a> • <a href="/" target="_blank" rel="noreferrer">Root</a>
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);