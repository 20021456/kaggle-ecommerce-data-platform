# infra/ — Infrastructure as Code

## OVERVIEW

Infrastructure templates for Docker, Terraform, Kubernetes, and CI/CD. Mostly scaffolded from `data_platform_standard.md`.

## STRUCTURE

```
infra/
├── docker/
│   ├── docker-compose.yml        # Full infra stack (alternative to root compose)
│   ├── docker-compose.dokploy.yml # Dokploy-specific compose
│   └── Dockerfile.airflow         # Custom Airflow image
├── terraform/                     # Terraform modules (scaffolded)
├── kubernetes/                    # K8s manifests (scaffolded)
└── ci_cd/                         # CI/CD templates (scaffolded, no GitHub Actions)
```

## NOTES

- Root `docker-compose.yml` is the primary local dev compose — `infra/docker/docker-compose.yml` is a duplicate/alternative
- No GitHub Actions workflows exist yet — `ci_cd/` is a placeholder per the standard template
- `Dockerfile.airflow` provides custom Airflow image if needed beyond the stock `apache/airflow:2.8.1`
- Terraform and Kubernetes directories are empty scaffolds from the standard template
