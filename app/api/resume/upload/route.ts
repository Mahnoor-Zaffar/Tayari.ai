import { NextRequest, NextResponse } from 'next/server';
import { createSupabaseServerClient } from '@/lib/supabase/server';
import { createClient } from '@supabase/supabase-js';
import { generateEmbeddings } from '@/backend/services/embeddings';
import { checkRateLimit } from '@/lib/rate-limit';

const CHUNK_SIZE = 2000;
const CHUNK_OVERLAP = 200;

function chunkText(text: string): string[] {
  const chunks: string[] = [];
  let start = 0;
  while (start < text.length) {
    const end = Math.min(start + CHUNK_SIZE, text.length);
    chunks.push(text.slice(start, end));
    start += CHUNK_SIZE - CHUNK_OVERLAP;
  }
  return chunks;
}

async function extractPdfText(buffer: Buffer): Promise<string> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mod: any = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const data = new Uint8Array(buffer);
  const doc = await mod.getDocument({ data }).promise;

  let text = '';
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i);
    const content = await page.getTextContent();
    text += content.items.map((item: { str: string }) => item.str).join(' ') + '\n';
  }
  return text.trim();
}

export async function POST(req: NextRequest) {
  const ip = req.headers.get('x-forwarded-for') ?? 'unknown';
  const { allowed, retryAfter } = checkRateLimit(`resume-upload:${ip}`);
  if (!allowed) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429, headers: { 'Retry-After': String(retryAfter) } },
    );
  }

  const supabase = await createSupabaseServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Unauthorised' }, { status: 401 });
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return NextResponse.json({ error: 'Failed to parse form data' }, { status: 400 });
  }

  const file = form.get('resume');
  if (!(file instanceof Blob)) {
    return NextResponse.json({ error: 'Missing or invalid "resume" field' }, { status: 400 });
  }

  if (file.type !== 'application/pdf' && !file.name?.endsWith('.pdf')) {
    return NextResponse.json({ error: 'Only PDF files are supported' }, { status: 400 });
  }

  let text: string;
  try {
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    text = await extractPdfText(buffer);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'PDF parsing failed';
    return NextResponse.json({ error: message }, { status: 500 });
  }

  if (!text.trim()) {
    return NextResponse.json({ error: 'No extractable text found in PDF' }, { status: 400 });
  }

  const chunks = chunkText(text);

  const serviceClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  );

  const inserted: { id: number; content: string }[] = [];

  const validChunks = chunks.filter((c) => c.trim());

  try {
    const embeddings = await generateEmbeddings(validChunks);

    for (let i = 0; i < validChunks.length; i++) {
      const { data, error } = await serviceClient
        .from('resume_embeddings')
        .insert({
          user_id: user.id,
          content: validChunks[i],
          embedding: embeddings[i],
          metadata: { source: file instanceof File ? file.name : 'resume.pdf' },
        })
        .select('id, content')
        .single();

      if (error) throw error;
      inserted.push(data);
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Embedding or insert failed';
    console.error('[resume/upload] Error:', err);
    if (inserted.length > 0) {
      await serviceClient
        .from('resume_embeddings')
        .delete()
        .in('id', inserted.map((r) => r.id));
    }
    return NextResponse.json({ error: message, detail: err instanceof Error ? err.message : String(err) }, { status: 500 });
  }

  return NextResponse.json({
    success: true,
    chunks: inserted.length,
  });
}
