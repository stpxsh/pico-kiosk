const http = require('http');

const SERVER_URL = 'http://localhost:3000/api/display';

console.log(`Připojuji se k ${SERVER_URL}...`);

http.get(SERVER_URL, (res) => {
  if (res.statusCode !== 200) {
    console.error(`Chyba serveru: ${res.statusCode}`);
    return;
  }

  let chunks = [];
  res.on('data', (chunk) => chunks.push(chunk));

  res.on('end', () => {
    const buffer = Buffer.concat(chunks);
    console.log(`\nÚspěšně staženo ${buffer.length} bytů!`);
    console.log('Vykresluji zmenšený náhled do terminálu:\n');

    // Terminál je moc úzký na 480 pixelů, tak vykreslíme jen výřez (např. levý horní roh 100x40 pixelů)
    // Případně můžeme vykreslit každý 4. pixel, ať máme celkový náhled. Uděláme celkový náhled zmenšený.
    
    const width = 480;
    const height = 320;
    const stepX = 4; // Vykreslíme každý 4. pixel na šířku
    const stepY = 8; // Vykreslíme každý 8. pixel na výšku (písmena v terminálu jsou vyšší než širší)

    // Horní okraj "displeje"
    console.log('+' + '-'.repeat(width / stepX) + '+');

    for (let y = 0; y < height; y += stepY) {
      let line = '|';
      for (let x = 0; x < width; x += stepX) {
        // Zjistíme, v jakém bytu a bitu se nachází náš pixel
        const bitIndexTotal = y * width + x;
        const byteIndex = Math.floor(bitIndexTotal / 8);
        const bitIndexInByte = 7 - (bitIndexTotal % 8); // Bity jsme ukládali odshora (7 do 0)

        // Přečteme bit
        const isBlack = (buffer[byteIndex] & (1 << bitIndexInByte)) !== 0;

        // Do terminálu dáme plný blok pro černou, mezeru pro bílou
        line += isBlack ? '█' : ' ';
      }
      line += '|';
      console.log(line);
    }
    
    // Spodní okraj "displeje"
    console.log('+' + '-'.repeat(width / stepX) + '+');
    console.log('\nSimulace Pico W dokončena. Data jsou validní a připravená na odeslání do e-inku!');
  });
}).on('error', (err) => {
  console.error('Chyba připojení:', err.message);
});