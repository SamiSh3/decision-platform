# Deployment

Production runs `docker-compose.prod.yml` on a single server, from a checkout at
`/opt/decision-platform`. Every push to `main` that passes CI is deployed
automatically by `.github/workflows/deploy.yml`, which connects over SSH and runs
`scripts/deploy.sh` (rebuild, migrate, restart, health check). It can also be
started by hand from the Actions tab (**Deploy → Run workflow**).

## One-time server setup

Run as root on the server:

```bash
command -v git >/dev/null || (apt-get update && apt-get install -y git)
command -v docker >/dev/null || (curl -fsSL https://get.docker.com | sh)

git clone https://github.com/SamiSh3/decision-platform.git /opt/decision-platform
cd /opt/decision-platform

DBPASS=$(openssl rand -hex 16); JWT=$(openssl rand -hex 32)
cp .env.example .env
sed -i "s/^APP_ENV=.*/APP_ENV=production/; s/^APP_DEBUG=.*/APP_DEBUG=false/; \
s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DBPASS/; \
s#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg://decision_user:$DBPASS@db:5432/decision_platform#; \
s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT/" .env

bash scripts/deploy.sh
```

Edit `BACKEND_CORS_ORIGINS` in `.env` to list the origins that will call the API.

## Deploy key for GitHub Actions

On the server, create a key used only by the deploy workflow:

```bash
ssh-keygen -t ed25519 -N "" -C "github-deploy" -f ~/.ssh/github_deploy
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy   # copy this into the SERVER_SSH_KEY secret
```

Then add these repository secrets (Settings → Secrets and variables → Actions):

| Secret           | Value                                           |
|------------------|-------------------------------------------------|
| `SERVER_HOST`    | Server IP or hostname                           |
| `SERVER_USER`    | SSH user (e.g. `root`)                          |
| `SERVER_SSH_KEY` | Contents of `~/.ssh/github_deploy` (private key) |
| `SERVER_PORT`    | Optional, defaults to `22`                      |

## Notes

- The server checkout is reset to `origin/main` on every deploy; do not edit files
  there except `.env`.
- The database port is not published; use
  `docker compose -f docker-compose.prod.yml exec db psql -U decision_user decision_platform`.
- `scripts/seed.py` creates demo users with a public password; do not run it in
  production unless you change those passwords afterwards.
