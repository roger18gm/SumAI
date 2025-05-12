import { defineConfig } from "vite";
import { resolve } from "path";
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss()
  ],
  build: {
    rollupOptions: {
      input: {
        popup: resolve(__dirname, "popup.html"),
        permission: resolve(__dirname, "permission.html"),
      },
      output: {
        entryFileNames: "[name].js",
      },
    },
  },
});
