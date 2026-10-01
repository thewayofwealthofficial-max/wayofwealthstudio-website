// 20:00 UK every day: Telegram round-up of the free tools (who opened, how far they got, where they stopped).
// Runs every hour at :05 (schedule in netlify.toml) and only sends in the 20:00 UK hour, so it follows the
// clock change by itself. Netlify's scheduler is on time; GitHub's ran the old quiz job 4 times in a day.

const { connectLambda, getStore } = require('@netlify/blobs');
const { ukDate, telegram, rollup } = require('./lib/magnet-events');
const { ukHour } = require('./lib/sequence-core');

exports.handler = async (event) => {
  if (ukHour() !== 20) return { statusCode: 200, body: 'not 20:00 UK' };
  connectLambda(event);
  await telegram(await rollup(getStore('magnet-events'), ukDate()));
  return { statusCode: 200, body: 'sent' };
};
