// MASTER candidate, 25.10.2026 05:49 TSI. Pure calculation; never publishes.
const uncertain = new Set(['SUBMITTING', 'UNKNOWN', 'RECONCILIATION_REQUIRED']);
export function istanbulDay(value) {
  if (typeof value !== 'string' || !/(?:Z|[+-]\d{2}:\d{2})$/.test(value)) throw Error('EXPLICIT_TIMEZONE_REQUIRED');
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) throw Error('INVALID_PUBLICATION_TIME');
  return new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Istanbul',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
}
export function dailyAdmission(inventory, journal, now, targetAt) {
  if (!inventory?.complete || !inventory?.queueComplete || inventory.allPathsCovered !== true) throw Error('DAILY_PUBLICATION_BUDGET_UNVERIFIED');
  if (!Array.isArray(inventory.published) || !Array.isArray(inventory.queued) || !Array.isArray(journal?.items)) throw Error('DAILY_INVENTORY_INVALID');
  if (!targetAt) throw Error('TARGET_PUBLICATION_TIME_UNVERIFIED');
  const today=istanbulDay(now), day=istanbulDay(targetAt), reservations=new Map();
  if (day < today) throw Error('TARGET_PUBLICATION_DAY_IN_PAST');
  const remember=(key,date)=>{
    if (reservations.has(key) && reservations.get(key)!==date) throw Error('PUBLICATION_DAY_CONFLICT');
    reservations.set(key,date);
  };
  for (const post of inventory.published) {
    if (!post.tumblrId || !post.publishedAt) throw Error('DAILY_PUBLICATION_TIME_UNVERIFIED');
    remember('post:'+post.tumblrId,istanbulDay(post.publishedAt));
  }
  for (const post of inventory.queued) {
    if (!post.tumblrId || !post.scheduledAt) throw Error('DAILY_PUBLICATION_TIME_UNVERIFIED');
    remember('post:'+post.tumblrId,istanbulDay(post.scheduledAt));
  }
  for (const row of journal.items) {
    if (!uncertain.has(row.status)) continue;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(row.reservedDay||'') || row.reservedDay < today) throw Error('UNCERTAIN_PUBLICATION_REQUIRES_RECONCILIATION');
    if (!row.tumblrId && !row.id) throw Error('RESERVATION_ID_MISSING');
    remember(row.tumblrId?'post:'+row.tumblrId:'job:'+row.id,row.reservedDay);
  }
  const used=[...reservations.values()].filter(date=>date===day).length;
  return {day,used,remaining:Math.max(0,3-used)};
}
