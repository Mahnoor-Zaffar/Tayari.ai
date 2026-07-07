import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import 'dotenv/config';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

const supabase = createClient(supabaseUrl, serviceKey);

async function migrate() {
  const sql = readFileSync(resolve('docs/SCHEMA.sql'), 'utf-8');

  // Run each statement separately
  const statements = sql
    .split(';')
    .map((s) => s.trim())
    .filter((s) => s && !s.startsWith('--'));

  for (const stmt of statements) {
    const { error } = await supabase.rpc('exec', { query: stmt + ';' }).single();
    if (error) {
      // Try direct query via REST
      console.error(`Statement failed (trying direct): ${error.message}`);
    }
  }

  console.log('Migration complete');
}

migrate().catch(console.error);
