# dokploy/ — Production Deployment

## OVERVIEW

Dokploy-based deployment with two projects: shared databases and application. Includes a minimal VPS profile.

## STRUCTURE

```
dokploy/
├── shared-databases/
│   └── docker-compose.yml    # Postgres, ClickHouse, Redis, MinIO, Kafka + healthchecks
├── application/
│   └── docker-compose.yml    # API service + Traefik routing + TLS
├── minimal/
│   ├── docker-compose.yml    # Lean profile (2 vCPU / 4GB RAM)
│   ├── deploy.sh             # Quick deploy script
│   └── init-scripts/         # DB init SQL
├── databases/                # Alternative DB configs
└── README.md                 # Deployment overview
```

## DEPLOYMENT FLOW

1. Create two Dokploy projects: `shared-databases` and `application`
2. Deploy `shared-databases` first — wait for healthchecks
3. Deploy `application` — connects to shared-databases network
4. API available via Traefik with automatic TLS

## CONVENTIONS

- Environment vars drive all config — no hardcoded values in compose files
- Services share `economic-network` Docker network
- `minimal/` profile removes: ClickHouse, Kafka, MinIO, Prometheus, Airflow
- Use `scripts/deploy-dokploy.sh` for automated deployment
