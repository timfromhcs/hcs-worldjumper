import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    chunkSizeWarningLimit: 3000,
  },
  server: {
    port: 8080,
    host: true
  },
  preview: {
    port: 4173,
    host: true
  }
});
