const express = require('express');
const puppeteer = require('puppeteer');
const sharp = require('sharp');
const getConfig = require('./config');

const app = express();
const config = getConfig();
const { server, source, display, puppeteer: puppeteerConfig } = config;

// Servírujeme statické soubory (náš HTML rozvrh) ze složky 'public'
app.use(express.static(server.publicDir));

async function generateDisplayPayload() {
  const browser = await puppeteer.launch(puppeteerConfig);

  const page = await browser.newPage();
  await page.setViewport({ width: display.width, height: display.height });

  await page.goto(source.pageUrl, { waitUntil: 'networkidle0' });

  const screenshotBuffer = await page.screenshot();
  await browser.close();

  const { data } = await sharp(screenshotBuffer)
    .resize(display.width, display.height)
    .grayscale()
    .threshold(display.threshold)
    .raw()
    .toBuffer({ resolveWithObject: true });

  const packedBuffer = Buffer.alloc(data.length / 8);
  for (let i = 0; i < data.length; i += 8) {
    let byte = 0;
    for (let bit = 0; bit < 8; bit++) {
      if (data[i + bit] === 0) { // Cokoliv černé (0) bude bit 1
        byte |= (1 << (7 - bit));
      }
    }
    packedBuffer[i / 8] = byte;
  }

  return packedBuffer;
}

app.get('/api/display', async (req, res) => {
  try {
    console.log(`[${new Date().toISOString()}] Generuji obraz pro Pico W...`);
    const payload = await generateDisplayPayload();
    res.set('Content-Type', 'application/octet-stream');
    res.set('Content-Length', payload.length);
    res.send(payload);
    console.log(`Odeslano: ${payload.length} bytu.`);
  } catch (error) {
    console.error('Chyba:', error);
    res.status(500).send('Server error');
  }
});

app.listen(server.port, server.host, () => {
  console.log(`Server bezi na ${server.host}:${server.port}`);
  console.log(`Zdrojova stranka pro render: ${source.pageUrl}`);
  console.log(`Náhled HTML: http://localhost:${server.port}`);
  console.log(`Endpoint pro Pico: http://localhost:${server.port}/api/display`);
});