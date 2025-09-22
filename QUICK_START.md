# 🚀 Quick Start Guide

## 1. Start Backend
```bash
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 2. Start Frontend  
```bash
cd frontend
npm run dev
```

## 3. Test Backend is Running
Open: http://localhost:8000/health

Should return:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

## 4. Test Frontend
Open: http://localhost:3000

## 5. Add OpenRouter API Key
1. Sign in with Clerk
2. Go to Settings
3. Add your OpenRouter API key
4. Click Save

## 🔧 Troubleshooting

**Backend 404 Error:**
- Make sure backend is running on port 8000
- Check: http://localhost:8000/health
- Check backend console for errors

**Frontend Clerk Error:**
- Make sure .env file has NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
- Restart frontend after env changes

**API Key Save Error:**
- Make sure both backend and frontend are running
- Check browser console for errors
- Verify CORS is working