# Ruby AI — Web App

Mobile-responsive web version of Ruby AI. Deployable on Vercel.

## Deploy to Vercel

1. Push this `web/` directory to a Git repo (or use the monorepo root).
2. On Vercel, import the project. Set:
   - **Root Directory**: `web/` (if deployed from monorepo)
   - **Framework**: Other
   - **Build Command**: (none)
   - **Output Directory**: (default)
3. Add environment variables in Vercel dashboard:
   - `OPENROUTER_API_KEY` — your OpenRouter API key (required)
   - `OPENROUTER_MODEL` — model name (default: `deepseek/deepseek-v4-flash`)
   - `SITE_URL` — your deployed URL (e.g. `https://ruby-ai.vercel.app`)
   - `SITE_NAME` — site name (default: `Ruby AI`)
4. Deploy.

## Local Development

```bash
cd web
pip install -r api/requirements.txt
uvicorn api.index:app --reload --port 8000
open http://localhost:8000
```

## Features

- Mobile-responsive dark-theme chat UI
- Real-time LLM chat via OpenRouter (DeepSeek V4 Flash)
- Web search via DuckDuckGo
- URL fetching
- Conversation persistence (browser localStorage)
- Works offline for history browsing
- Optional client-side API key (sent per-request, not stored on server)
