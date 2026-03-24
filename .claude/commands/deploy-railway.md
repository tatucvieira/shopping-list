# Deploy to Railway

You are a deployment assistant. Deploy the current project (or a subdirectory) to Railway using their GraphQL API v2.

## Required Setup

The user must have `RAILWAY_TOKEN` set as an environment variable or as a secret in GitHub. If the token is not available, tell the user:

> You need a Railway API token. Go to https://railway.com/account/tokens, create one scoped to your workspace, and set it:
> ```
> export RAILWAY_TOKEN="your-token-here"
> ```
> Or add it to `.claude/settings.local.json` under `env`.

## Input: $ARGUMENTS

The user may provide arguments like:
- Project name (default: current repo name)
- Subdirectory to deploy (default: repo root)
- Example: `/deploy-railway shopping-list shopping-list/` → project name "shopping-list", root dir "shopping-list"

Parse the arguments: first word = project name, second word = root directory (optional).

## Deployment Steps

Use the Railway GraphQL API at `https://backboard.railway.app/graphql/v2` with Bearer token auth.

### Step 1: Check existing projects
```graphql
{ projects { edges { node { id name services { edges { node { id name } } } } } } }
```
If a project with the same name already exists, ask the user if they want to reuse it or create a new one.

### Step 2: Create project (if needed)
```graphql
mutation { projectCreate(input: { name: "PROJECT_NAME" }) { id name } }
```

### Step 3: Get environment ID
```graphql
{ project(id: "PROJECT_ID") { environments { edges { node { id name } } } } }
```
Use the first environment (usually "production").

### Step 4: Create service linked to GitHub repo
Detect the GitHub repo from `git remote -v`. Then:
```graphql
mutation { serviceCreate(input: { name: "web", projectId: "PROJECT_ID", source: { repo: "OWNER/REPO" } }) { id name } }
```

### Step 5: Set environment variables
If a root directory was specified:
```graphql
mutation { variableUpsert(input: { projectId: "PROJECT_ID", environmentId: "ENV_ID", serviceId: "SERVICE_ID", name: "RAILWAY_ROOT_DIRECTORY", value: "ROOT_DIR" }) }
```

Always set PORT=8080:
```graphql
mutation { variableUpsert(input: { projectId: "PROJECT_ID", environmentId: "ENV_ID", serviceId: "SERVICE_ID", name: "PORT", value: "8080" }) }
```

If the project has a `.env.example` or known env vars, ask the user if they want to set them.

### Step 6: Generate public domain
```graphql
mutation { serviceDomainCreate(input: { serviceId: "SERVICE_ID", environmentId: "ENV_ID" }) { domain } }
```

### Step 7: Report

Print a clear summary:
```
✅ Railway Deploy Complete
   Project:  PROJECT_NAME (PROJECT_ID)
   Service:  SERVICE_ID
   Domain:   https://DOMAIN
   Status:   Railway will auto-build from the GitHub repo
```

## GraphQL Helper

Use curl for all API calls:
```bash
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "YOUR_QUERY"}'
```

## Error Handling

- If any API call returns an error, show the full error to the user and suggest fixes
- If "Not Authorized", the token may be invalid or lack permissions — tell user to check token scope
- If project creation fails, it may be a naming conflict — suggest a different name

## Important Notes

- NEVER hardcode tokens in files or commits
- Always use `$RAILWAY_TOKEN` environment variable
- The GitHub repo must be public OR the Railway account must have GitHub integration enabled
- Railway auto-deploys on push to the connected branch (usually main)
