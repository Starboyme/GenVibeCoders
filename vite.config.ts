import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@auth": path.resolve(__dirname, "srv/src/auth"), // external folder
      "@": path.resolve(__dirname, "ui/src") // so @/components works too
    }
  }
});
