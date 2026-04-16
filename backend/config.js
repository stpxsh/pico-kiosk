const path = require('path');

function parseIntEnv(name, fallback) {
    const value = process.env[name];
    if (!value) return fallback;

    const parsed = Number.parseInt(value, 10);
    return Number.isNaN(parsed) ? fallback : parsed;
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function ensureLeadingSlash(value) {
    return value.startsWith('/') ? value : `/${value}`;
}

function getConfig() {
    const port = parseIntEnv('PORT', 3000);
    const sourcePagePath = ensureLeadingSlash(process.env.SOURCE_PAGE_PATH || '/index.html');

    const displayWidth = parseIntEnv('DISPLAY_WIDTH', 800);
    const displayHeight = parseIntEnv('DISPLAY_HEIGHT', 480);

    return {
        server: {
            host: process.env.HOST || '0.0.0.0',
            port,
            publicDir: process.env.PUBLIC_DIR || path.join(__dirname, 'public')
        },
        source: {
            pagePath: sourcePagePath,
            pageUrl: process.env.SOURCE_PAGE_URL || `http://localhost:${port}${sourcePagePath}`
        },
        display: {
            width: displayWidth,
            height: displayHeight,
            threshold: clamp(parseIntEnv('DISPLAY_THRESHOLD', 128), 0, 255)
        },
        puppeteer: {
            headless: process.env.PUPPETEER_HEADLESS || 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
            executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined
        }
    };
}

module.exports = getConfig;
