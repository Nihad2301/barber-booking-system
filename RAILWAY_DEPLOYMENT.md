# Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- Neon PostgreSQL database (already set up for development)
- Git repository with this code pushed to GitHub

## Environment Variables

Set these in Railway's environment variables section (Settings > Variables):

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `SECRET_KEY` | JWT signing secret (generate a strong random string) | Use `openssl rand -hex 32` or similar |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |

**Important:** Use the Neon connection string from your production Neon instance, not the development one.

## Deployment Steps

### 1. Connect GitHub Repository to Railway
1. Go to Railway (https://railway.app)
2. Click "New Project" > "Deploy from GitHub repo"
3. Select your barber-booking-system repository
4. Railway will automatically detect it as a Python project

### 2. Configure the Project
1. Once the project is created, click on the project settings
2. Go to the "Variables" tab
3. Add the environment variables listed above
4. Make sure `DATABASE_URL` points to your **production** Neon database

### 3. Deploy
1. Railway will automatically deploy on push to the connected branch
2. Monitor the deployment logs in the Railway dashboard
3. Once deployed, Railway will provide a public URL (e.g., `https://barber-booking-system.up.railway.app`)

### 4. Run Alembic Migrations on Production Neon

**Before the first deployment**, run migrations against your production Neon database:

```bash
# Set your production DATABASE_URL
export DATABASE_URL="postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Run migrations
alembic upgrade head
```

**Alternative:** You can also run this via Railway's console if you prefer:
1. Go to your project in Railway
2. Click on the "Neon PostgreSQL" service (if you're using Railway's managed Postgres)
3. Open the console and run: `alembic upgrade head`

**Note:** Since you're using external Neon (not Railway's managed Postgres), run the migration command locally with the production DATABASE_URL set.

### 5. Verify Deployment
1. Visit the Railway-provided URL
2. Check the root endpoint returns: `{"message": "Barber Booking System API"}`
3. Test a few endpoints to ensure connectivity to Neon works

## Post-Deployment Checklist

- [ ] Environment variables configured in Railway
- [ ] Alembic migrations run against production Neon
- [ ] Root endpoint accessible
- [ ] Test authentication (login/register)
- [ ] Test booking creation
- [ ] Verify scheduler is running (check logs for "nightly_slot_generation")

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` includes `?sslmode=require` for Neon
- Check Neon database is accepting connections from Railway's IP
- Review Railway deployment logs for connection errors

### Migration Issues
- Ensure you're running migrations against the **production** Neon instance
- Check `alembic.ini` is pointing to the correct DATABASE_URL
- Verify all migration files are committed to Git

### Scheduler Not Running
- Check logs for APScheduler startup messages
- Verify the startup event is firing (should see "scheduler.start()" in logs)

## Notes

- Railway automatically handles HTTPS
- The app uses a background scheduler (APScheduler) for nightly slot generation
- Railway will rebuild and redeploy on every push to the connected branch
- Monitor logs in Railway dashboard for runtime errors
