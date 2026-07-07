import { NextRequest, NextResponse } from 'next/server';
import { createSupabaseServerClient } from '@/lib/supabase/server';
import { createClient } from '@supabase/supabase-js';
import { generateEmbeddings } from '@/backend/services/embeddings';
import { spawn } from 'child_process';

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
  const scriptPath = process.cwd() + '/scripts/extract_pdf_text.py';
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', [scriptPath]);
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];

    proc.stdout.on('data', (chunk: Buffer) => stdout.push(chunk));
    proc.stderr.on('data', (chunk: Buffer) => stderr.push(chunk));

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(Buffer.concat(stderr).toString()));
      } else {
        resolve(Buffer.concat(stdout).toString());
      }
    });

    proc.on('error', reject);
    proc.stdin.end(buffer);
  });
}

export async function POST(req: NextRequest) {
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
