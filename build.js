// build.js
import { build } from 'esbuild'
build({
  entryPoints: ['src/index.js'],
  bundle: true,
  platform: 'node',
  format: 'cjs',               // output CommonJS for require()
  outfile: 'dist/index.cjs',
  external: ['canvas'],      // whatever native modules you have
})