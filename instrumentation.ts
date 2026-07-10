export async function register() {
  const { generateEmbedding } = await import('./src/backend/services/embeddings');
  try {
    await generateEmbedding('warmup');
    console.log('[tayari] Embedding model preloaded');
  } catch (err) {
    console.error('[tayari] Failed to preload embedding model:', err);
  }
}
