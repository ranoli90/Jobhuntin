/**
 * Optimized Vite Configuration
 * Microsoft-level implementation with performance optimizations
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  
  // Build optimizations
  build: {
    target: 'es2020',
    minify: 'terser',
    sourcemap: true,
    
    // Code splitting optimization
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['framer-motion', 'lucide-react'],
          'vendor-query': ['@tanstack/react-query'],
          
          // Feature chunks
          'auth': ['./src/hooks/useAuth.ts', './src/services/magicLinkService.ts'],
          'onboarding': ['./src/pages/app/Onboarding.tsx', './src/hooks/useOnboarding.ts'],
          'dashboard': ['./src/pages/Dashboard.tsx', './src/hooks/useApplications.ts'],
          'jobs': ['./src/hooks/useJobs.ts', './src/hooks/useJobMatching.ts'],
          'team': ['./src/hooks/useTeamManagement.ts'],
          
          // Remaining code
          'common': ['./src/lib', './src/components/ui'],
        },
      },
      
      // External dependencies that shouldn't be bundled
      external: (id) => {
        // Keep React-related dependencies internal for better tree-shaking
        return false;
      },
    },
    
    // Terser options for optimal minification
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'],
      },
      mangle: {
        safari10: true,
      },
    },
    
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
    
    // Asset optimization
    assetsInlineLimit: 4096,
  },
  
  // Development optimizations
  server: {
    fs: {
      // Allow serving files from project root
      allow: ['..'],
    },
  },
  
  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'framer-motion',
      'lucide-react',
    ],
    
    exclude: [
      // Exclude development dependencies
      'vite',
      '@vitejs/plugin-react',
    ],
  },
  
  // Resolution optimizations
  resolve: {
    alias: {
      // Path aliases for cleaner imports
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@hooks': resolve(__dirname, './src/hooks'),
      '@lib': resolve(__dirname, './src/lib'),
      '@pages': resolve(__dirname, './src/pages'),
      '@services': resolve(__dirname, './src/services'),
      '@utils': resolve(__dirname, './src/utils'),
    },
  },
  
  // CSS optimizations
  css: {
    devSourcemap: true,
    
    // PostCSS plugins for optimization
    postcss: {
      plugins: [
        // Add future PostCSS optimizations here
      ],
    },
  },
  
  // Preview configuration
  preview: {
    port: 4173,
    strictPort: true,
  },
  
  // Environment variables
  define: {
    // Feature flags
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
    __PROD__: JSON.stringify(process.env.NODE_ENV === 'production'),
    __VERSION__: JSON.stringify(process.env.npm_package_version),
  },
  
  // Experimental features
  experimental: {
    renderBuiltUrl: '/',
    // Enable build optimizations
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@tanstack/react-query',
        'framer-motion',
      ],
    },
  },
});
