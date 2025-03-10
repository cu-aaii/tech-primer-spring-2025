import { defineConfig } from 'vite';

// Output directory is set to the FastAPI static directory
const outDir = '../app/toolbot/static';

export default defineConfig({
  root: '.',
  build: {
    outDir,
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        main: 'index.html',
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
