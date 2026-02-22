const fs = require('fs');
const path = require('path');

const SITEMAP = path.join(__dirname, 'public', 'sitemap.xml');
const BASE_URL = 'https://jobhuntin.com';
const INDEXNOW_KEY = '2021b89b3147e09e54b705189f2082d8446ce96c';

const content = fs.readFileSync(SITEMAP, 'utf-8');
const matches = content.match(/<loc>(.*?)<\/loc>/g) || [];
const urls = matches.map(m => m.replace(/<\/?loc>/g, ''));

console.log("Found", urls.length, "URLs to submit");

const batchSize = 100;
let submitted = 0;
let errors = 0;

async function submitBatch(batch) {
    const payload = {
        host: 'jobhuntin.com',
        key: INDEXNOW_KEY,
        keyLocation: `${BASE_URL}/${INDEXNOW_KEY}.txt`,
        urlList: batch
    };
    
    const endpoints = [
        'https://api.indexnow.org/indexnow',
        'https://www.bing.com/indexnow'
    ];
    
    for (const endpoint of endpoints) {
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (res.ok || res.status === 202) {
                return true;
            }
        } catch (e) {
            continue;
        }
    }
    return false;
}

async function main() {
    console.log("\n🚀 Submitting", urls.length, "URLs via IndexNow...");
    
    for (let i = 0; i < urls.length; i += batchSize) {
        const batch = urls.slice(i, i + batchSize);
        const success = await submitBatch(batch);
        
        if (success) {
            submitted += batch.length;
            console.log("✅ Batch", Math.floor(i / batchSize) + 1 + "/" + Math.ceil(urls.length / batchSize) + ":", batch.length, "URLs submitted");
        } else {
            errors += batch.length;
            console.log("❌ Batch", Math.floor(i / batchSize) + 1, "failed");
        }
        
        await new Promise(r => setTimeout(r, 200));
    }
    
    console.log(`\n📊 Complete!`);
    console.log("   ✅ Submitted:", submitted);
    console.log("   ❌ Errors:", errors);
    console.log("   📈 Success Rate:", ((submitted / urls.length) * 100).toFixed(1) + "%");
}

main();
