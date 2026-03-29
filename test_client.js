const http = require('http');
const fs = require('fs');

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

        if (process.argv.includes('--raw')) {
            const path = require('path');
            const outPath = path.join(__dirname, 'bin_out', 'payload.bin');

            if (!fs.existsSync(path.dirname(outPath))) {
                fs.mkdirSync(path.dirname(outPath), { recursive: true });
            }

            fs.writeFileSync(outPath, buffer);
            console.log(`Soubor ${outPath} byl úspěšně uložen.`);

            const first32 = Array.from(buffer.slice(0, 32))
                .map(b => '0x' + b.toString(16).padStart(2, '0').toUpperCase())
                .join(', ');
            console.log('Zde je prvních 32 bytů tohoto bufferu:');
            console.log(first32);
            console.log('\nSimulace Pico W dokončena (raw data uložena).');
        } else {
            console.log('Vykresluji zmenšený náhled do terminálu:\n');

            // Terminál je moc úzký na 480 pixelů, tak vykreslíme jen výřez (např. levý horní roh 100x40 pixelů)
            // Případně můžeme vykreslit každý 4. pixel, ať máme celkový náhled. Uděláme celkový náhled zmenšený.

            const width = 480;
            const height = 320;

            // Funkce pro získání pixelu z našeho packedBufferu
            const getPixel = (x, y) => {
                if (x >= width || y >= height) return false;
                const bitIndexTotal = y * width + x;
                const byteIndex = Math.floor(bitIndexTotal / 8);
                const bitOffset = 7 - (bitIndexTotal % 8);
                return (buffer[byteIndex] & (1 << bitOffset)) !== 0;
            };

            console.log('+' + '-'.repeat(width / 2) + '+');
            // Braillovo písmo: 2 sloupce, 4 řádky (2x4 matice)
            // Mapování teček: 
            // 1 4
            // 2 5
            // 3 6
            // 7 8
            for (let y = 0; y < height; y += 4) {
                let line = '|';
                for (let x = 0; x < width; x += 2) {
                    let code = 0x2800; // Base Unicode for Braille
                    if (getPixel(x, y)) code |= 0x01;     // dot 1
                    if (getPixel(x, y + 1)) code |= 0x02; // dot 2
                    if (getPixel(x, y + 2)) code |= 0x04; // dot 3
                    if (getPixel(x + 1, y)) code |= 0x08; // dot 4
                    if (getPixel(x + 1, y + 1)) code |= 0x10; // dot 5
                    if (getPixel(x + 1, y + 2)) code |= 0x20; // dot 6
                    if (getPixel(x, y + 3)) code |= 0x40; // dot 7
                    if (getPixel(x + 1, y + 3)) code |= 0x80; // dot 8
                    line += String.fromCharCode(code);
                }
                line += '|';
                console.log(line);
            }
            console.log('+' + '-'.repeat(width / 2) + '+');
            console.log('\nSimulace Pico W dokončena. Data jsou validní a připravená na odeslání do e-inku!');
        }
    });
}).on('error', (err) => {
    console.error('Chyba připojení:', err.message);
});