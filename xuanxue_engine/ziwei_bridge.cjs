const fs = require('fs');
const iztro = require('iztro');

function readPayload() {
  const raw = fs.readFileSync(0, 'utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

function main() {
  const payload = readPayload();
  const solarDate = String(payload.solarDate || '').trim();
  const gender = String(payload.gender || '').trim();
  const targetDateTime = String(payload.targetDateTime || '').trim();
  const timeIndex = Number(payload.timeIndex);

  if (!solarDate) {
    throw new Error('solarDate is required');
  }
  if (!Number.isInteger(timeIndex) || timeIndex < 0 || timeIndex > 12) {
    throw new Error('timeIndex must be an integer between 0 and 12');
  }
  if (!gender) {
    throw new Error('gender is required');
  }

  const chart = iztro.astro.bySolar(solarDate, timeIndex, gender, true, 'zh-CN');
  const horoscope = chart.horoscope(targetDateTime ? new Date(targetDateTime) : new Date());
  process.stdout.write(JSON.stringify({ chart, horoscope }));
}

try {
  main();
} catch (error) {
  const message = error && error.message ? error.message : String(error);
  process.stderr.write(message);
  process.exit(1);
}
