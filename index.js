const TikTokScraper = require('tiktok-scraper');
const axios = require('axios');
const fs = require('fs');

const USER = process.env.TT_USER;
const WEBHOOK = process.env.DISCORD_WEBHOOK;

const FILE = 'last.json';

async function getLast() {
  if (!fs.existsSync(FILE)) return null;
  return JSON.parse(fs.readFileSync(FILE)).id;
}

function saveLast(id) {
  fs.writeFileSync(FILE, JSON.stringify({ id }));
}

async function check() {
  const posts = await TikTokScraper.user(USER, { number: 1 });
  const video = posts.collector[0];

  const last = getLast();

if (!last) {
  console.log('Primeira execução → enviando último vídeo');

  await axios.post(WEBHOOK, {
    content: `🧪 TESTE (último vídeo):\nhttps://www.tiktok.com/@${USER}/video/${video.id}`
  });

  saveLast(video.id);
  return;
}

if (video.id !== last) {
    console.log('Novo vídeo detectado!');

    await axios.post(WEBHOOK, {
      content: `🔥 Novo vídeo:\nhttps://www.tiktok.com/@${USER}/video/${video.id}`
    });

    saveLast(video.id);
  } else {
    console.log('Nada novo.');
  }
}

check();
