# 🚀 Deployment Guide

## Quick Deploy to Vercel

### 1. Deploy Frontend to Vercel

**Option A: One-Click Deploy**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Adilmohd04/agentic_research)

**Option B: Manual Deploy**
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import from GitHub: `https://github.com/Adilmohd04/agentic_research`
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 2. Environment Variables in Vercel

Add these in Vercel Dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_Y29uY2lzZS1zcXVpZC0yNi5jbGVyay5hY2NvdW50cy5kZXYk
NEXT_PUBLIC_API_URL=https://your-backend-url.vercel.app
NEXT_PUBLIC_WS_URL=wss://your-backend-url.vercel.app
```

### 3. Deploy Backend (Optional)

For full functionality, deploy the Python backend:

**Option A: Vercel (Serverless)**
- Create new Vercel project for backend
- Use Python runtime
- Set build command: `pip install -r requirements.txt`

**Option B: Railway/Render**
- Better for Python backends
- Connect GitHub repo
- Auto-deploy on push

### 4. Features Available

**Frontend Only (Vercel):**
✅ Voice-to-text (browser-based)  
✅ Text-to-speech (browser-based)  
✅ Chat interface  
✅ Authentication (Clerk)  
❌ API key saving (needs backend)  
❌ Document upload (needs backend)  
❌ RAG search (needs backend)  

**With Backend:**
✅ All features enabled  
✅ Encrypted API key storage  
✅ Document upload & search  
✅ RAG system  
✅ Multi-user isolation  

## 🔧 Local Development

```bash
# Start backend
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend
cd frontend
npm run dev
```

## 🌐 Live Demo

Once deployed, your app will be available at:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-backend.vercel.app` (if deployed)

## 🔑 API Keys Needed

- **Clerk**: For authentication
- **OpenRouter**: For AI models
- **Supabase**: For database (optional)

## 📝 Notes

- The app works without backend (limited features)
- Voice features work in browser without backend
- For production, deploy both frontend and backend
- All user data is isolated and encrypted