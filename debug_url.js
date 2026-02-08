
const https = require('https');

function checkUrl(url) {
  console.log(`Checking ${url}...`);
  https.get(url, (res) => {
    console.log(`Status: ${res.statusCode}`);
    console.log('Headers:', JSON.stringify(res.headers, null, 2));
    
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });
    
    res.on('end', () => {
      console.log('Body Preview:', data.substring(0, 500));
    });
  }).on('error', (e) => {
    console.error(`Error: ${e.message}`);
  });
}

checkUrl('https://jobhuntin.com/app/onboarding');
checkUrl('https://jobhuntin.com/health');
checkUrl('https://sorce-web.onrender.com/app/onboarding');
