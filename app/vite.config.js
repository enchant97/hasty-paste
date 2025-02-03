import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  build: {
    manifest: true,
    rollupOptions: {
      input: "./main.js",
    }
  }
})
