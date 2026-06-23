import fs from 'node:fs';
import { calculateDaliuren } from 'taibu-core/daliuren';

function readPayload() {
  const raw = fs.readFileSync(0, 'utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

async function main() {
  const payload = readPayload();
  const date = String(payload.date || '').trim();
  const hour = Number(payload.hour);
  const minute = Number(payload.minute ?? 0);
  const timezone = String(payload.timezone || 'Asia/Shanghai').trim() || 'Asia/Shanghai';
  const question = String(payload.question || '').trim();
  const birthYear = payload.birthYear == null ? undefined : Number(payload.birthYear);
  const gender = payload.gender == null ? undefined : String(payload.gender).trim();

  if (!date) {
    throw new Error('date is required');
  }
  if (!Number.isInteger(hour)) {
    throw new Error('hour is required');
  }

  const chart = await calculateDaliuren({
    date,
    hour,
    minute,
    timezone,
    question,
    birthYear,
    gender,
  });
  process.stdout.write(JSON.stringify(chart));
}

main().catch((error) => {
  const message = error && error.message ? error.message : String(error);
  process.stderr.write(message);
  process.exit(1);
});
