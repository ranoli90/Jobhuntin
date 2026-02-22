
const fs = require('fs');
const path = require('path');

const API_KEY = 'rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa';
const WEB_SERVICE_ID = 'srv-d63spbogjchc739akan0';
const API_SERVICE_ID = 'srv-d63l79hr0fns73boblag';

const serviceAccount = fs.readFileSync(path.resolve(__dirname, '../service-account.json'), 'utf8');
const compactServiceAccount = JSON.stringify(JSON.parse(serviceAccount));

const newVars = [
    { key: 'GOOGLE_SERVICE_ACCOUNT_KEY', value: compactServiceAccount },
    { key: 'LLM_API_KEY', value: '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' },
    { key: 'VITE_GA_ID', value: 'G-P1QLYH3M13' }
];

async function updateService(serviceId, vars) {
    console.log("Updating service", serviceId, "...");

    const currentResp = await fetch(`https://api.render.com/v1/services/${serviceId}/env-vars`, {
        headers: { 'Authorization': `Bearer ${API_KEY}` }
    });

    if (!currentResp.ok) {
        console.error("Failed to fetch env vars for", serviceId);
        return;
    }

    const currentData = await currentResp.json();
    const currentVars = currentData.map(d => ({ key: d.envVar.key, value: d.envVar.value }));

    // Merge
    const mergedVars = [...currentVars];
    for (const nv of vars) {
        const idx = mergedVars.findIndex(v => v.key === nv.key);
        if (idx > -1) {
            mergedVars[idx].value = nv.value;
        } else {
            mergedVars.push(nv);
        }
    }

    const putResp = await fetch(`https://api.render.com/v1/services/${serviceId}/env-vars`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(mergedVars)
    });

    if (!putResp.ok) {
        const err = await putResp.text();
        console.error("Failed to PUT env vars for", serviceId, ":", putResp.status, err);
    } else {
        console.log("Successfully updated all env vars for", serviceId);
    }
}

async function main() {
    await updateService(WEB_SERVICE_ID, newVars);
    await updateService(API_SERVICE_ID, newVars);
}

main();
