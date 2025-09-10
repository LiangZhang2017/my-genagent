import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // OLD: base: '/ui/'
  base: './'   // <-- relative URLs so it works inside /api/agent-proxy/<id>/ui/
});