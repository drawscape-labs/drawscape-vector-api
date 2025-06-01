# Drawscape Vector API

API built in flask to serve Drawscape SVG functionality.

## Dev
Using Python 3.12 with Docker

## Installation & Development

### Docker Setup (Required)
```
make build
```

## Run Dev

Start the application:
```
make up
```

View logs:
```
make logs
```

Stop the application:
```
make down
```

## Development Commands

### Primary Commands
- `make build` - Build the Docker image
- `make up` - Start the application (foreground)
- `make down` - Stop the application
- `make logs` - View application logs
- `make shell` - Get a shell inside the container

### Full Docker Commands
- `make docker-build` - Build the Docker image
- `make docker-up` - Start the application (foreground)
- `make docker-up-detached` - Start the application (background)
- `make docker-down` - Stop the application
- `make docker-logs` - View application logs
- `make docker-shell` - Get a shell inside the container
- `make docker-rebuild` - Rebuild and restart everything
- `make docker-clean` - Clean up containers and images

## Environment Variables

Copy `env.example` to `.env` and update as needed for local development.

## Application Access

Once running, the API will be available at: `http://localhost:5000`

## Production Deployment

### Heroku Deployment
See [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) for detailed instructions on deploying to Heroku.

Quick deploy:
```bash
# Add Redis addon
heroku addons:create heroku-redis:mini

# Set production environment
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Scale worker if needed
heroku ps:scale worker=1
```