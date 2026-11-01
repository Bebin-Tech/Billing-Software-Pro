# Deployment prerequisites

Deployment is not yet performed. No Vercel/Render project, managed MySQL credentials, SMTP account, domain, or authorized GST provider was configured during implementation. Do not use the current limited slice for production accounting.

## Target configuration

- Frontend: Vercel, root `frontend`, `npm ci`, `npm run build`, output `dist`. Rewrite `/api/:path*` to your Render backend and use a same-origin `VITE_API_URL=/api/v1`; add an SPA fallback for client routes. Do not send refresh cookies directly cross-site with SameSite Strict. Verify origin forwarding and cookie behavior against the actual deployment.
- Backend: Render Python web service, root `backend`, install `requirements.txt`; pre-deploy `alembic upgrade head`; start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Python 3.13 recommended. Use one worker until shared rate limiting and cross-worker verification are in place.
- MySQL: managed MySQL 8 with verified TLS, dedicated least-privilege runtime user, separate migration credentials, automated encrypted backups and point-in-time recovery. SQLAlchemy's DATABASE_URL must carry the provider's TLS parameters. Never use the development Docker database as production hosting.
- Secret environment: random JWT_SECRET, DATABASE_URL, SECURE_COOKIES=true, REGISTRATION_ENABLED=false after onboarding, CORS_ORIGINS containing only the production frontend origin. No secrets may use VITE_ prefix.
- Readiness: `/health/ready`; monitor error rates, latency, failed login attempts and refresh reuse events. Configure centralized JSON logs and error tracking without passwords/tokens.

## Release gates

All remaining phases, real SMTP delivery, shared rate limits, production dependency audit, browser accessibility checks and complete MySQL API/E2E coverage must pass. Local MySQL migration round trip, schema comparison, concurrent numbering/payment and database tenant-reference tests have passed for the implemented slice. Verify invoice PDF layout and mandatory particulars with a qualified practitioner. Exercise backup restore in an isolated environment; record RPO/RTO and conduct restore drills. Verify HTTPS, cookie flags, production proxy routing, logout/reuse revocation, CORS/CSRF, and two-company isolation on the deployed URLs.
