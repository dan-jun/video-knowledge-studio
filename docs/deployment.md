# Deployment modes

## 1. Personal local instance — recommended

Each person runs the app on their own computer:

```text
Alice computer: 127.0.0.1:7870 → Alice course packs and local state
Bob computer:   127.0.0.1:7870 → Bob course packs and local state
```

The numeric address is intentionally the same, but it always points to the current
computer. No user can reach another user's instance or files.

```powershell
python -m vks
```

or:

```powershell
python scripts/bootstrap.py start --open
```

## 2. LAN or single-user remote server

Set a strong password before binding to `0.0.0.0`:

```text
VKS_HOST=0.0.0.0
VKS_PASSWORD=<strong password>
```

Use HTTPS through a reverse proxy. This still represents one shared workspace, not
separate user accounts.

## 3. Docker

```bash
export VKS_PASSWORD='choose-a-strong-password'
docker compose up --build
```

The Compose file mounts `packs/` read-only and `data/` writable. It refuses to start
unless `VKS_PASSWORD` is supplied.

## 4. Public multi-user SaaS — not implemented

A shared website where Alice and Bob register separate accounts requires new work:

- user identity and authentication;
- database ownership fields on courses, episodes, annotations and revisions;
- per-user object storage and quotas;
- ownership checks on every media and frame request;
- signed media URLs;
- uploads, transcoding and deletion policy;
- audit logs, rate limits, backup and billing.

A single deployment password is not tenant isolation. Do not market it as such.
