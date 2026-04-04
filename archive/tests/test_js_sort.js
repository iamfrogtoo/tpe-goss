const fs = require('fs');

function parseTime(d, t) {
    if (!t || !d) return Number.MAX_SAFE_INTEGER;
    const currentYear = new Date().getFullYear();
    return Date.parse(`${currentYear}/${d} ${t}`);
}

const mockData = [
    { type: 'ARR', date: '03/07', time: '00:05:00', code: 'ZE885' },
    { type: 'ARR', date: '03/06', time: '04:20:00', code: 'EVA633' },
    { type: 'DEP', date: '03/07', time: '01:05:00', code: 'CAL5991' },
    { type: 'DEP', date: '03/06', time: '04:09:00', code: 'Y87912' }
];

for (const f of mockData) {
    f.sortTime = parseTime(f.date, f.time);
    console.log(`${f.date} ${f.time} -> ${f.sortTime}`);
}

mockData.sort((a, b) => a.sortTime - b.sortTime);

console.log('Sorted Result:');
for (const f of mockData) {
    console.log(`- ${f.date} ${f.time} ${f.code}`);
}
