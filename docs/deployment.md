# Deployment prerequisites

## Current status — 2 November 2026

Frontend deployed and verified: https://gst-billing-pro.vercel.app

Vercel project: gst-billing-pro, team bebin-dotms-projects. Deployment dpl_4QKJ9QtADzjNpuqiqhQNGGmisGs1, source commit 379f591db1868cb945e1a706433cef7dc9464f7d. HTML responds 200; the API gateway correctly responds 503 because BACKEND_URL is unset. This is a frontend-only deployment. Login, tenant access and billing are not online yet. Deployment protection was preserved.

Render and managed MySQL are not set up (confirmed by the user). SMTP and authorized GST services are also unconfigured. Do not use this incomplete application for production accounting.

## Complete the backend connection

1. Open [the Render Blueprint installer](https://render.com/deploy?repo=https://github.com/Bebin-Tech/Billing-Software-Pro). Review the committed `render.yaml`. It selects a free Python web service and does not purchase a database.
2. Provision managed MySQL 8 with backups and certificate-verified TLS. Enter the provider's SQLAlchemy connection URL directly as DATABASE_URL in Render; never paste it into chat or GitHub. Use a separate migration account if supported.
3. Set FRONTEND_URL and CORS_ORIGINS to `https://gst-billing-pro.vercel.app` in Render. The blueprint generates JWT_SECRET and enables Secure cookies. Registration defaults to disabled. Temporarily enable it for administrator onboarding, then disable it again.
4. Deploy Render. Startup applies Alembic migrations before starting one Uvicorn worker. Confirm `/health/ready` returns 200.
5. In the Vercel project's production environment, set server-only BACKEND_URL to the Render HTTPS origin, without a path (e.g. `https://your-service.onrender.com`). Redeploy the frontend. The gateway forwards authorization, tenant selection, Origin and cookies, preserving refresh cookie rotation. It never places database credentials in the browser.
6. Verify registration/onboarding, sign-in, company access, invoice issue/PDF/payment, reports, refresh/logout and two-company isolation against the real deployment before any business use.

Gateway tests: `node --test scripts/gateway.test.mjs` (three passed). Frontend component tests (five) and production build passed before this deployment.

## Target configuration

- Frontend: Vercel, root `frontend`, `npm ci`, `npm run build`, output `dist`. Rewrite `/api/:path*` to your Render backend and use a same-origin `VITE_API_URL=/api/v1`; add an SPA fallback for client routes. Do not send refresh cookies directly cross-site with SameSite Strict. Verify origin forwarding and cookie behavior against the actual deployment.
- Backend: Render Python web service, root `backend`, install `requirements.txt`; pre-deploy `alembic upgrade head`; start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Python 3.13 recommended. Use one worker until shared rate limiting and cross-worker verification are in place.
- MySQL: managed MySQL 8 with verified TLS, dedicated least-privilege runtime user, separate migration credentials, automated encrypted backups and point-in-time recovery. SQLAlchemy's DATABASE_URL must carry the provider's TLS parameters. Never use the development Docker database as production hosting.
- Secret environment: random JWT_SECRET, DATABASE_URL, SECURE_COOKIES=true, REGISTRATION_ENABLED=false after onboarding, CORS_ORIGINS containing only the production frontend origin. No secrets may use VITE_ prefix.
- Readiness: `/health/ready`; monitor error rates, latency, failed login attempts and refresh reuse events. Configure centralized JSON logs and error tracking without passwords/tokens.

## Release gates

All remaining phases, real SMTP delivery, shared rate limits, production dependency audit, browser accessibility checks and complete MySQL API/E2E coverage must pass. Local MySQL migration round trip, schema comparison, concurrent numbering/payment and database tenant-reference tests have passed for the implemented slice. Verify invoice PDF layout and mandatory particulars with a qualified practitioner. Exercise backup restore in an isolated environment; record RPO/RTO and conduct restore drills. Verify HTTPS, cookie flags, production proxy routing, logout/reuse revocation, CORS/CSRF, and two-company isolation on the deployed URLs.
