let pipeline: ((texts: string[]) => Promise<number[][]>) | null = null;

async function getPipeline(): Promise<(texts: string[]) => Promise<number[][]>> {
  if (pipeline) return pipeline;

  const { pipeline: pipe } = await import('@xenova/transformers');
  const p = await pipe('feature-extraction', 'Xenova/all-MiniLM-L6-v2', {
    quantized: true,
  });

  pipeline = async (texts: string[]) => {
    const result = await p(texts, { pooling: 'mean', normalize: true });
    return result.tolist() as number[][];
  };

  return pipeline;
}

export async function generateEmbedding(text: string): Promise<number[]> {
  const embed = await getPipeline();
  const result = await embed([text]);
  return result[0];
}

export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  const embed = await getPipeline();
  return embed(texts);
}
