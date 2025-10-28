# Reddit Automation Setup Guide

This guide explains how to set up automated Reddit comment responses for ProjectCollatz using GitHub Actions.

## Overview

The automation system:
- Runs every 2 hours (configurable)
- Monitors specified Reddit posts for new comments
- Uses OpenAI GPT-4o-mini to generate contextual responses
- Automatically replies to comments that haven't been responded to yet
- Logs all responses to prevent duplicates

## Prerequisites

1. **Reddit Account**: Your Reddit account (e.g., u/WeeklyExamination)
2. **Reddit API Access**: Create a Reddit app to get API credentials
3. **OpenAI API Key**: For generating intelligent responses
4. **GitHub Repository**: This repository with Actions enabled

## Step 1: Create Reddit API Application

1. Go to https://www.reddit.com/prefs/apps
2. Scroll to "developed applications" and click "create another app..."
3. Fill in the form:
   - **name**: ProjectCollatz Bot
   - **App type**: Select "script"
   - **description**: Automated responder for ProjectCollatz posts
   - **about url**: https://github.com/jaylouisw/projectcollatz
   - **redirect uri**: http://localhost:8080 (required but not used)
4. Click "create app"
5. Note down:
   - **client_id**: The string under "personal use script"
   - **client_secret**: The secret string shown

## Step 2: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy and save it securely (you won't see it again)

## Step 3: Get Reddit Post IDs

For each post you want to monitor, extract the post ID from the URL:

**Example URLs:**
- `https://reddit.com/r/Collatz/comments/1ohur9c/the_collatz_conjecture_from_boinc_scandal_to/`
  - **Post ID**: `1ohur9c`
- `https://reddit.com/r/ipfs/comments/1ohurlc/the_collatz_conjecture_from_boinc_scandal_to/`
  - **Post ID**: `1ohurlc`
- `https://reddit.com/r/DistributedComputing/comments/1ohuv5r/the_collatz_conjecture_from_boinc_scandal_to/`
  - **Post ID**: `1ohuv5r`

**Current ProjectCollatz post IDs:**
```
1ohur9c,1ohurlc,1ohuv5r
```

## Step 4: Configure GitHub Secrets

Go to your GitHub repository settings and add these secrets:

1. Go to: **Settings** → **Secrets and variables** → **Actions**
2. Click "New repository secret" for each of the following:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `REDDIT_CLIENT_ID` | Your Reddit app client ID | `abc123xyz` |
| `REDDIT_CLIENT_SECRET` | Your Reddit app secret | `secret123abc` |
| `REDDIT_USERNAME` | Your Reddit username | `WeeklyExamination` |
| `REDDIT_PASSWORD` | Your Reddit password | `your_password` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |
| `REDDIT_POST_IDS` | Comma-separated post IDs | `1ohur9c,1ohurlc,1ohuv5r` |

## Step 5: Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, enable GitHub Actions
3. The workflow will appear as "Reddit Comment Responder"

## Step 6: Test the Workflow

### Manual Test:
1. Go to **Actions** → **Reddit Comment Responder**
2. Click "Run workflow" → "Run workflow" button
3. Monitor the execution logs

### Check Logs:
1. Click on the running workflow
2. Expand "Run Reddit responder" to see detailed output
3. Download artifacts to see the response log

## Workflow Configuration

### Schedule
The workflow runs every 2 hours by default. To change this:

Edit `.github/workflows/reddit-responder.yml`:
```yaml
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
  # - cron: '0 * * * *'  # Every hour
  # - cron: '*/30 * * * *'  # Every 30 minutes
```

**Note**: GitHub Actions has a minimum 5-minute interval for scheduled workflows.

### Response Behavior

The bot classifies comments into categories and responds appropriately:

- **Technical**: Detailed answers about architecture, implementation, GPU support, IPFS
- **Skeptical**: Transparent responses addressing trust/security concerns
- **Casual**: Brief, friendly acknowledgments
- **Neutral**: Balanced informative responses

### Rate Limiting

The bot includes:
- 2-second delay between responses (configurable in `reddit_responder.py`)
- Duplicate response prevention (logs responded comment IDs)
- Reddit API rate limit compliance (PRAW handles this automatically)

## Monitoring and Maintenance

### Check Response Logs
Download the `reddit-response-log` artifact from workflow runs to see:
- Which comments were responded to
- Last run timestamp
- Full history of responses

### Disable Automation
To temporarily disable:
1. Go to **Actions** → **Reddit Comment Responder**
2. Click "..." → "Disable workflow"

Or delete/rename the workflow file:
```bash
git mv .github/workflows/reddit-responder.yml .github/workflows/reddit-responder.yml.disabled
git commit -m "Disable Reddit automation"
git push
```

## Local Testing

Test the script locally before deploying:

```bash
# Install dependencies
pip install praw openai python-dotenv

# Create .env file with your credentials
cat > .env << EOF
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
REDDIT_POST_IDS=1ohur9c,1ohurlc,1ohuv5r
EOF

# Run the script
python reddit_responder.py
```

## Customization

### Modify Response Tone
Edit `reddit_responder.py` → `_generate_response()` → `system_prompt`

### Change Comment Classification
Edit `reddit_responder.py` → `_classify_comment()` to adjust keywords

### Adjust Response Length
Edit `reddit_responder.py` → `_generate_response()` → `max_tokens` parameter

### Add More Posts
Update the `REDDIT_POST_IDS` secret with additional comma-separated post IDs

## Troubleshooting

### Authentication Errors
- Verify Reddit credentials are correct
- Check that Reddit app type is "script", not "web app"
- Ensure 2FA is disabled on Reddit account (or use app-specific password)

### No Responses Generated
- Check OpenAI API key is valid and has credits
- Review workflow logs for errors
- Verify post IDs are correct (no `t3_` prefix needed)

### Rate Limiting
- Reddit allows ~60 API calls per minute
- GitHub Actions free tier: 2,000 minutes/month
- OpenAI API has usage limits based on your tier

## Cost Estimates

### OpenAI API Costs (GPT-4o-mini):
- Input: ~$0.15 per 1M tokens
- Output: ~$0.60 per 1M tokens
- Typical response: ~$0.0002 per comment (very low cost)

### GitHub Actions:
- Free tier: 2,000 minutes/month for private repos
- This workflow: ~1 minute per run = ~360 runs/month
- **Comfortably within free tier**

## Security Notes

1. **Never commit credentials** to the repository
2. Use GitHub Secrets for all sensitive data
3. Rotate API keys periodically
4. Monitor API usage for suspicious activity
5. Review bot responses regularly to ensure quality

## Support

For issues with:
- **Reddit API**: https://www.reddit.com/r/redditdev
- **OpenAI API**: https://help.openai.com
- **GitHub Actions**: https://docs.github.com/actions
- **ProjectCollatz**: https://github.com/jaylouisw/projectcollatz/issues
