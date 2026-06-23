import fs from 'node:fs';
import { calculateQimen } from 'taibu-core/qimen';

function readPayload() {
  const raw = fs.readFileSync(0, 'utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

async function main() {
  const payload = readPayload();
  const year = Number(payload.year);
  const month = Number(payload.month);
  const day = Number(payload.day);
  const hour = Number(payload.hour);
  const minute = Number(payload.minute ?? 0);
  const timezone = String(payload.timezone || 'Asia/Shanghai').trim() || 'Asia/Shanghai';
  const question = String(payload.question || '').trim();
  const panType = String(payload.panType || 'zhuan').trim() || 'zhuan';
  const juMethod = String(payload.juMethod || 'chaibu').trim() || 'chaibu';
  const zhiFuJiGong = String(payload.zhiFuJiGong || 'ji_liuyi').trim() || 'ji_liuyi';

  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day) || !Number.isInteger(hour)) {
    throw new Error('year/month/day/hour are required integers');
  }

  const chart = await calculateQimen({
    year,
    month,
    day,
    hour,
    minute,
    timezone,
    question,
    panType,
    juMethod,
    zhiFuJiGong,
  });
  process.stdout.write(JSON.stringify(chart));
}

main().catch((error) => {
  const message = error && error.message ? error.message : String(error);
  process.stderr.write(message);
  process.exit(1);
});
