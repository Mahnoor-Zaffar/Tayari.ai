import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname),
      '@/backend': path.resolve(__dirname, 'src/backend'),
      '@/frontend': path.resolve(__dirname, 'src/frontend'),
      '@/types': path.resolve(__dirname, 'types'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['**/*.test.ts'],
  },
});
