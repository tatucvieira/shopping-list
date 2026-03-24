# Railway Deploy Skill

**Maturity:** L2 (Practiced)
**Last used:** 2026-03-24

## What it does

Deploys any application to Railway via their GraphQL API v2. No CLI needed — works entirely through API calls with `curl`.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/deploy-railway [name] [dir]` | Create project, service, set vars, generate domain |
| `/railway-status [command]` | Check status, logs, redeploy, manage projects |

## Prerequisites

1. **Railway account** at https://railway.com
2. **API Token** — create at https://railway.com/account/tokens (scope to your workspace)
3. **Set token** as environment variable:
   ```bash
   export RAILWAY_TOKEN="your-token"
   ```

## Usage Examples

```
# Deploy current repo as "my-app"
/deploy-railway my-app

# Deploy a subdirectory
/deploy-railway shopping-list shopping-list/

# Check all projects
/railway-status

# Redeploy a project
/railway-status redeploy my-app
```

## How it works

1. Uses Railway GraphQL API (`https://backboard.railway.app/graphql/v2`)
2. Creates project → gets environment → creates service linked to GitHub repo → sets env vars → generates domain
3. Railway auto-deploys from GitHub on every push

## Key API Patterns

```bash
# Generic GraphQL call pattern
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ projects { edges { node { id name } } } }"}'
```

## Lessons Learned

- Railway CLI (`railway` command) often fails with team tokens — GraphQL API is more reliable
- Always set `PORT=8080` as env var
- Use `RAILWAY_ROOT_DIRECTORY` for monorepo subdirectories
- The `me` query doesn't work with workspace-scoped tokens (returns "Not Authorized") — this is expected, use `projects` query instead
- GitHub repo must be public or Railway must have GitHub app installed
