// build.js
import { build } from 'esbuild'

// Run the build
build({
  entryPoints: ['src/index.js'],
  bundle: true,
  platform: 'node',
  format: 'cjs',               // output CommonJS for require()
  outfile: 'dist/index.cjs',
  external: ['canvas'],      // whatever native modules you have
}).then(() => {
  console.log('✅ Build completed successfully!')
}).catch(err => {
  console.error('❌ Build failed:', err)
  process.exit(1)
})