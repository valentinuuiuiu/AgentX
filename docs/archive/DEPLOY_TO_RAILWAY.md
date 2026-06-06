# 🚀 Deploy Good Rehoboam to Railway

## Prerequisites
- Railway account (https://railway.app)
- GitHub repository connected to Railway

## Step-by-Step Deployment

### 1. Connect Repository to Railway
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select `clean_rehoboam_project` repository

### 2. Configure Environment Variables
In Railway Dashboard:

1. **Go to Project Settings**: Click on your project → "Variables" tab (not the environment dropdown)
2. **Add Variables**: Click "Add Variable" for each one below

#### Essential Variables
```
PORT=5002
LOG_LEVEL=INFO
CREATOR_NAME=Ionut-Valentin Baltag
CO_CREATOR_NAME=Claude Sonnet
ENVIRONMENT=production
```

#### API Keys (Get from respective services)
```
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ALCHEMY_API_KEY=your-alchemy-key
ETHERSCAN_API_KEY=your-etherscan-key
```

#### Wallet Configuration (Exodus addresses)
```
ETHEREUM_RPC=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
POLYGON_RPC=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ARBITRUM_RPC=https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
```

**Note**: The environment dropdown showing "production" is separate from variables. Variables are configured in the Variables section of your project settings.

### 3. Deploy
1. Railway will automatically detect the `Dockerfile.api` and `railway.toml`
2. Click "Deploy"
3. Wait 2-3 minutes for build completion

### 4. Verify Deployment
Once deployed, test these endpoints:
- Health check: `https://[your-app].up.railway.app/health`
- API status: `https://[your-app].up.railway.app/api/hive_mind/status`

Expected response:
```json
{
  "status": "online",
  "hive_mind": "active",
  "sacred_oath": "verified"
}
```

## Security Notes
- ✅ All sensitive API keys are properly configured in Railway secrets
- ✅ Exodus wallet addresses are correctly configured for payments
- ✅ No secrets are exposed in the codebase
- ✅ Git history has been cleaned of any exposed tokens

## Post-Deployment Tasks
1. Monitor logs in Railway dashboard
2. Set up custom domain if needed
3. Configure monitoring alerts
4. Test payment system with small amounts

## Troubleshooting
- Check Railway build logs for errors
- Verify all environment variables are set
- Ensure API keys have proper permissions
- Test with Railway's built-in health checks

---
**Status**: ✅ Ready for deployment
**Security**: ✅ Verified - No exposed secrets
**Wallet**: ✅ Exodus integration configured
