const fs = require('fs');

function readPayload() {
  const raw = fs.readFileSync(0, 'utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

function toHourDecimal(timeText) {
  const parts = String(timeText || '').trim().split(':');
  if (parts.length < 2) {
    throw new Error('birthTime must be in HH:MM format');
  }
  const hour = Number(parts[0]);
  const minute = Number(parts[1]);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) {
    throw new Error('birthTime contains invalid hour or minute');
  }
  return hour + minute / 60;
}

async function main() {
  const natal = await import('natalengine');
  const payload = readPayload();
  const birthDate = String(payload.birthDate || '').trim();
  const birthTime = String(payload.birthTime || '').trim();
  const tzStr = String(payload.tzStr || '').trim();
  const nodeType = String(payload.nodeType || 'true').trim().toLowerCase() || 'true';

  if (!birthDate) {
    throw new Error('birthDate is required');
  }
  if (!birthTime) {
    throw new Error('birthTime is required');
  }
  if (!tzStr) {
    throw new Error('tzStr is required');
  }

  const birthHour = toHourDecimal(birthTime);
  const utcOffset = natal.resolveUtcOffset(birthDate, birthTime, tzStr);
  const chart = natal.calculateHumanDesign(birthDate, birthHour, utcOffset, { nodeType });
  process.stdout.write(JSON.stringify({ utcOffset, chart }));
}

main().catch((error) => {
  const message = error && error.message ? error.message : String(error);
  process.stderr.write(message);
  process.exit(1);
});
