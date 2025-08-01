import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { convertImageBlob } from '../lib/convert'
import { ImageMode, ImageModeUtil, OutputMode } from '../lib/enums';
import fetch from 'node-fetch';
import { loadImage } from 'canvas';

const upload = multer();
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.post(
  '/convert',
  upload.single('image'),
  async (req, res) => {
    try {
      const q = req.body;
      let fileBuf;
      if (q.url) {
        const response = await fetch(q.url);
        if (!response.ok) throw new Error(`Failed to fetch image from URL: ${response.statusText}`);
        const arrayBuf = await response.arrayBuffer();
        fileBuf = Buffer.from(arrayBuf);
      } else {
        fileBuf = req.file.buffer;
      }

      // parse / validate your options
      const cf = ImageMode[q.cf];
      const output = q.output;
      const dither = q.dither === 'true';
      const bigEndian = q.bigEndian === 'true';

      // map output string → enums
      let outputMode = OutputMode.C;
      let binaryFormat;
      if (output === 'c_array') {
        outputMode = OutputMode.C;
      } else {
        outputMode = OutputMode.BIN;
        if (ImageModeUtil.isTrueColor(cf)) {
          const map = {
            bin_332: ImageMode.ICF_TRUE_COLOR_ARGB8332,
            bin_565: ImageMode.ICF_TRUE_COLOR_ARGB8565,
            bin_565_swap: ImageMode.ICF_TRUE_COLOR_ARGB8565_RBSWAP,
            bin_888: ImageMode.ICF_TRUE_COLOR_ARGB8888,
          };
          binaryFormat = map[output];
        }
      }

      // Prepare input: for RAW modes use Uint8Array, otherwise decode and optionally resize image
      let inputData;
      if (cf === ImageMode.CF_RAW || cf === ImageMode.CF_RAW_ALPHA) {
        inputData = new Uint8Array(fileBuf);
      } else {
        // load original image (resize will be handled by convertImageBlob options)
        inputData = await loadImage(fileBuf);
      }
      // prepare conversion options, include resize hints if provided
      const opts = {
        cf,
        outputFormat: outputMode,
        binaryFormat,
        swapEndian: bigEndian,
        dith: dither,
        outName: 'converted',
      };
      if (q.maxSize) {
        console.log(`Resizing image to max size: ${q.maxSize}`);
        const [mw, mh] = q.maxSize.toLowerCase().split('x').map(n => parseInt(n, 10));
        if (!isNaN(mw) && !isNaN(mh)) {
          opts.overrideWidth = mw;
          opts.overrideHeight = mh;
        }
      }
      const result = await convertImageBlob(inputData, opts);

      if (outputMode === OutputMode.BIN) {
        res.setHeader('Content-Type', 'application/octet-stream');
        res.send(Buffer.from(result));
      } else {
        res.setHeader('Content-Type', 'text/plain; charset=utf-8');
        res.send(result);
      }
    } catch (e) {
      console.error(e);
      res.status(500).send(e.message);
    }
  }
);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`API listening on http://localhost:${PORT}`));