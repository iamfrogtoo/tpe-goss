const fs = require('fs');
const https = require('https');

const CSV_BAY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=214244940&single=true&output=csv";

https.get(CSV_BAY, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        const rows = data.split('\n').map(r => r.split(','));
        console.log(`Total rows: ${rows.length}`);
        console.log("First 5 rows:");
        for (let i = 0; i < Math.min(5, rows.length); i++) {
            console.log(rows[i]);
        }

        console.log("Rows for gate A7:");
        const a7Rows = rows.filter(r => r[0] === 'A7');
        a7Rows.forEach(r => console.log(r));

        console.log("Rows containing A7:");
        const containingA7 = rows.filter(r => r.some(c => c.includes('A7')));
        containingA7.forEach(r => console.log(r));

        console.log("Unique gates:");
        const gates = [...new Set(rows.slice(1).map(r => r[0]))].sort();
        console.log(gates.join(', '));
    });
}).on('error', err => console.error(err));
