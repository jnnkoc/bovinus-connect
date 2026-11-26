import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base './' = caminhos relativos (funciona em https://<usuario>.github.io/bovinus-connect/site/).
// O build vai para ../site, que é a pasta publicada.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: { outDir: '../site', emptyOutDir: true, assetsDir: 'assets' },
});
