# 🚀 Deploy Guide — StakeWave

## Free Hosting Stack

| Service | Purpose | Cost |
|---------|---------|------|
| Vercel | Frontend hosting | Free |
| Railway | Backend + Bot | Free (500h/month) |
| Supabase | PostgreSQL DB | Free (500MB) |
| Cloudflare | CDN + DNS | Free |

## Step 1: Deploy Backend (Railway)

1. Go to [railway.app](https://railway.app)
2. Login with GitHub
3. New Project → Deploy from GitHub repo
4. Select `StakeWave` repo
5. Root directory: `backend`
6. Add environment variables:
   - `BOT_TOKEN` = your bot token
   - `SECRET_KEY` = random string
   - `JWT_SECRET` = random string
7. Deploy!

## Step 2: Deploy Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com)
2. Login with GitHub
3. Import `StakeWave` repo
4. Root directory: `frontend`
5. Deploy!

## Step 3: Connect Bot to Mini App

1. Talk to @BotFather on Telegram
2. `/mybots` → Select your bot
3. Bot Settings → Menu Button
4. Set URL to your Vercel frontend URL

## Step 4: Set Webhook

After backend is deployed, visit:
```
https://your-backend-url.railway.app/set-webhook
```

Done! Your bot is live! 🎉
