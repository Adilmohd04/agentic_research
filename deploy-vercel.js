#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Preparing for Vercel deployment...\n');

// 1. Copy environment variables
console.log('📋 Setting up environment variables...');
const rootEnv = path.join(__dirname, '.env');
const frontendEnv = path.join(__dirname, 'frontend', '.env.local');

if (fs.existsSync(rootEnv)) {
  const envContent = fs.readFileSync(rootEnv, 'utf8');
  const publicVars = envContent
    .split('\n')
    .filter(line => line.startsWith('NEXT_PUBLIC_'))
    .join('\n');
  
  fs.writeFileSync(frontendEnv, `# Auto-generated for Vercel\n${publicVars}`);
  console.log('✅ Environment variables copied');
}

// 2. Create vercel.json for frontend-only deployment
const vercelConfig = {
  "name": "ai-rag-system",
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "env": {
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "pk_test_Y29uY2lzZS1zcXVpZC0yNi5jbGVyay5hY2NvdW50cy5kZXYk",
    "NEXT_PUBLIC_API_URL": "https://your-backend-url.vercel.app"
  }
};

fs.writeFileSync('vercel.json', JSON.stringify(vercelConfig, null, 2));
console.log('✅ Vercel config created');

console.log('\n🎯 Ready for Vercel deployment!');
console.log('\nNext steps:');
console.log('1. Run: vercel --prod');
console.log('2. Set environment variables in Vercel dashboard');
console.log('3. Deploy backend separately if needed');