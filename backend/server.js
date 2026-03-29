const express = require('express');
const puppeteer = require('puppeteer');
const sharp = require('sharp');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Servírujeme statické soubory (náš HTML rozvrh) ze složky 'public'
app.use(express.static(path.join(__dirname, 'public')));

async function generateDisplayPayload() {
  // Pro Puppeteer v Dockeru (Podmanu) musíme přidat argumenty pro vypnutí sandboxu
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || null // Použije systémový Chromium v Dockeru
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 480, height: 320 });
  
  // Řekneme Puppeteeru, ať si otevře stránku, kterou sami hostujeme!
  await page.goto(`http://localhost:${PORT}/index.html`, { waitUntil: 'networkidle0' });
  
  const screenshotBuffer = await page.screenshot();
  await browser.close();

  const { data } = await sharp(screenshotBuffer)
    .resize(480, 320)
    .grayscale()
    .threshold(128)
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

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server bezi na portu ${PORT}`);
  console.log(`Náhled HTML: http://localhost:${PORT}`);
  console.log(`Endpoint pro Pico: http://localhost:${PORT}/api/display`);
});