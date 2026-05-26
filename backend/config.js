const path = require('path');

const config = {
    server: {
        host: '0.0.0.0',
        port: 3000,
        publicDir: path.join(__dirname, 'public')
    },
    source: {
        pagePath: '/index.html',
        bakabridge: 'http://maturis.spss.local:4444/timetable',
        // pageUrl: 'http://localhost:3000/index.html'
        //pageUrl: 'https://spssol.cz'
    },
    display: {
        width: 800,
        height: 480,
        threshold: 128
    },
    puppeteer: {
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        executablePath: undefined
    }
};

module.exports = config;
