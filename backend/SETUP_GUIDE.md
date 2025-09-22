# AI Agenting Research - Setup Guide

## 🚀 Quick Start with OpenRouter

This project uses **OpenRouter** as the primary AI service provider, giving you access to multiple AI models through a single API key.

### 1. Get Your OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Go to your [API Keys section](https://openrouter.ai/keys)
4. Create a new API key
5. Copy your API key (starts with `sk-or-v1-...`)

### 2. Configure Your Environment

1. Open `backend/.env` file
2. Replace `your-openrouter-key-here` with your actual API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### 3. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. Start the Services

```bash
# Terminal 1 - Backend
cd backend
python src/main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 🧠 RAG System Features

### Supported Document Types
- **PDF** - Research papers, reports, manuals
- **DOCX** - Word documents, proposals
- **TXT** - Plain text files, code documentation
- **Markdown** - README files, technical docs
- **HTML** - Web pages, documentation

### Available AI Models (via OpenRouter)

#### OpenAI Models
- `gpt-4` - Most capable, best for complex reasoning
- `gpt-4-turbo` - Faster GPT-4 with larger context
- `gpt-3.5-turbo` - Fast and cost-effective

#### Anthropic Models
- `claude-3-opus` - Most capable Claude model
- `claude-3-sonnet` - Balanced performance and speed
- `claude-3-haiku` - Fastest Claude model

#### Other Popular Models
- `llama-2-70b` - Meta's open-source model
- `mixtral-8x7b` - Mistral's mixture of experts
- `gemini-pro` - Google's multimodal model

### RAG Workflow

1. **Upload Documents** - Add your knowledge base
2. **Automatic Processing** - Documents are chunked and vectorized
3. **Intelligent Search** - Find relevant information quickly
4. **AI-Powered Q&A** - Ask questions and get contextual answers
5. **Source Citations** - See exactly where answers come from

## 🔧 Configuration Options

### Model Selection
You can specify which model to use in the frontend or API calls:

```javascript
// Frontend example
const response = await fetch('/api/rag/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    question: "What is machine learning?",
    model: "gpt-4"  // Specify model
  })
});
```

### Environment Variables

```env
# Required
OPENROUTER_API_KEY=your-key-here

# Optional - Direct API access
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Model Configuration
DEFAULT_MODEL=openai/gpt-3.5-turbo
MAX_TOKENS=2000
TEMPERATURE=0.7
```

## 📊 Usage Examples

### 1. Research Assistant
Upload research papers and ask:
- "What are the main findings in this study?"
- "Compare the methodologies across these papers"
- "What are the limitations mentioned?"

### 2. Code Documentation
Upload code files and ask:
- "How does this authentication system work?"
- "What are the security considerations?"
- "Explain the database schema"

### 3. Business Analysis
Upload reports and ask:
- "What are the key performance indicators?"
- "Summarize the financial trends"
- "What risks are identified?"

## 🛠️ Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Check your `.env` file
   - Ensure the key starts with `sk-or-v1-`
   - Restart the backend server

2. **"Document upload failed"**
   - Check file format (PDF, DOCX, TXT, MD, HTML)
   - Ensure file size is reasonable (<10MB)
   - Check backend logs for details

3. **"Search returns no results"**
   - Upload documents first
   - Try different search terms
   - Check if documents were processed successfully

### Performance Tips

1. **Chunk Size**: Larger documents are automatically chunked for better retrieval
2. **Model Selection**: Use faster models (GPT-3.5, Claude Haiku) for quick queries
3. **Context Limit**: Limit context documents (3-5) for faster responses
4. **Batch Processing**: Upload multiple documents at once for efficiency

## 🔒 Security & Privacy

- API keys are stored securely in environment variables
- Documents are processed locally (not sent to external services for processing)
- Only relevant chunks are sent to AI models for answering
- All data stays within your infrastructure

## 📈 Monitoring & Analytics

The system provides:
- Document processing statistics
- Search performance metrics
- AI model usage tracking
- Response quality indicators

Access these through the RAG interface or API endpoints:
- `/api/rag/stats` - System statistics
- `/api/rag/documents` - Document library
- WebSocket updates for real-time monitoring

## 🚀 Advanced Features

### Custom Embeddings
Switch between local and cloud embeddings:
- Local: SentenceTransformers (free, private)
- Cloud: OpenAI embeddings (paid, higher quality)

### Multi-Model Responses
Compare answers from different models:
```javascript
const models = ['gpt-4', 'claude-3-sonnet', 'mixtral-8x7b'];
const responses = await Promise.all(
  models.map(model => askQuestion(question, model))
);
```

### Conversation Memory
The system maintains context across questions for natural conversations.

---

## 🎯 Next Steps

1. **Upload your first document** using the RAG interface
2. **Try different AI models** to see which works best for your use case
3. **Experiment with question types** - factual, analytical, creative
4. **Monitor performance** through the dashboard
5. **Scale up** by adding more documents and users

For more advanced configuration and API documentation, visit `/docs` when the backend is running.