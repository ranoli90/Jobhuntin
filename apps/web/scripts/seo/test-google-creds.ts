/**
 * test-google-creds.ts
 * 
 * Quick test to verify Google credentials and submit URLs
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { google } from 'googleapis';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('🔍 TESTING GOOGLE CREDENTIALS');
  console.log('='.repeat(60));

  const keyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  
  if (!keyEnv) {
    console.error('❌ GOOGLE_SERVICE_ACCOUNT_KEY not set');
    process.exit(1);
  }

  console.log(`📊 Key length: ${keyEnv.length}`);
  console.log(`📊 First 100 chars: ${keyEnv.substring(0, 100)}...`);
  console.log(`📊 Last 50 chars: ...${keyEnv.substring(keyEnv.length - 50)}`);
  
  // Try to parse
  let keyContent;
  try {
    keyContent = JSON.parse(keyEnv);
    console.log('\n✅ Successfully parsed as JSON');
  } catch (e) {
    console.log('\n❌ Could not parse as JSON string');
    console.log(`Error: ${e}`);
    
    // Try as file path
    try {
      if (fs.existsSync(keyEnv)) {
        keyContent = JSON.parse(fs.readFileSync(keyEnv, 'utf8'));
        console.log('✅ Loaded from file');
      } else {
        console.log(`❌ File not found: ${keyEnv}`);
        process.exit(1);
      }
    } catch (e2) {
      console.log(`❌ Could not load from file: ${e2}`);
      process.exit(1);
    }
  }

  // Check required fields
  console.log('\n📋 Checking required fields:');
  const requiredFields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email'];
  for (const field of requiredFields) {
    if (keyContent[field]) {
      if (field === 'private_key') {
        console.log(`   ✅ ${field}: ${keyContent[field].substring(0, 30)}...`);
      } else {
        console.log(`   ✅ ${field}: ${keyContent[field]}`);
      }
    } else {
      console.log(`   ❌ ${field}: MISSING`);
    }
  }

  // Try to authenticate
  console.log('\n🔐 Attempting authentication...');
  
  try {
    const jwtClient = new google.auth.JWT({
      email: keyContent.client_email,
      key: keyContent.private_key,
      scopes: ['https://www.googleapis.com/auth/indexing']
    });
    
    await jwtClient.authorize();
    console.log('✅ Authentication successful!');
    
    // Try a test submission
    const indexing = google.indexing({ version: 'v3', auth: jwtClient });
    
    const testUrl = 'https://jobhuntin.com/';
    console.log(`\n📤 Testing submission of: ${testUrl}`);
    
    const response = await indexing.urlNotifications.publish({
      requestBody: {
        url: testUrl,
        type: 'URL_UPDATED'
      }
    });
    
    console.log('✅ Test submission successful!');
    console.log(`📡 Response: ${JSON.stringify(response.data)}`);
    
  } catch (e: any) {
    console.log(`\n❌ Authentication failed: ${e.message}`);
    if (e.response?.data) {
      console.log(`📡 Error details: ${JSON.stringify(e.response.data)}`);
    }
    process.exit(1);
  }
  
  console.log('\n🎉 ALL TESTS PASSED!');
}

main().catch(console.error);
