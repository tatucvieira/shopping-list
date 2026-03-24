# Railway Status & Management

Check status, logs, and manage Railway deployments via GraphQL API v2.

## Required: `RAILWAY_TOKEN` environment variable

If not set, instruct user to go to https://railway.com/account/tokens.

## Input: $ARGUMENTS

Commands the user can pass:
- `status` (default) — List all projects and their services/domains
- `logs PROJECT_NAME` — Show recent deployment logs
- `delete PROJECT_NAME` — Delete a project (ask confirmation first!)
- `redeploy PROJECT_NAME` — Trigger a redeploy
- `domain PROJECT_NAME` — Show or create domain for a service
- `vars PROJECT_NAME` — List environment variables

## API Base

```
https://backboard.railway.app/graphql/v2
```
Auth: `Authorization: Bearer $RAILWAY_TOKEN`

## Queries

### List all projects with services and domains
```graphql
{
  projects {
    edges {
      node {
        id
        name
        services {
          edges {
            node {
              id
              name
              serviceInstances {
                edges {
                  node {
                    domains {
                      serviceDomains { domain }
                      customDomains { domain }
                    }
                  }
                }
              }
            }
          }
        }
        environments {
          edges {
            node { id name }
          }
        }
      }
    }
  }
}
```

### Get deployments for a service
```graphql
{
  deployments(
    input: { serviceId: "SERVICE_ID", environmentId: "ENV_ID" }
    first: 5
  ) {
    edges {
      node {
        id
        status
        createdAt
      }
    }
  }
}
```

### Trigger redeploy
```graphql
mutation {
  serviceInstanceRedeploy(
    serviceId: "SERVICE_ID"
    environmentId: "ENV_ID"
  )
}
```

### Delete project
```graphql
mutation { projectDelete(id: "PROJECT_ID") }
```

## Output Format

Always present results in a clean, readable format. Example:

```
📦 Railway Projects
┌─────────────────┬──────────┬─────────────────────────────────┐
│ Project         │ Service  │ Domain                          │
├─────────────────┼──────────┼─────────────────────────────────┤
│ shopping-list   │ web      │ web-production-xxx.up.railway.app│
└─────────────────┴──────────┴─────────────────────────────────┘
```
