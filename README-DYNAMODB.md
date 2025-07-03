# DynamoDB Local Setup for Tennis Meetup Bot

This guide explains how to set up and use DynamoDB Local for development and testing of the Tennis Meetup Bot.

## Prerequisites

- Docker and Docker Compose
- Python 3.13.2
- AWS CLI (optional, for direct interaction with DynamoDB Local)

## Setup

### 1. Start DynamoDB Local

```bash
# Navigate to the project directory
cd /path/to/meetup-bot

# Start DynamoDB Local using Docker Compose
cd docker/dev
docker-compose up -d dynamodb-local
```

This will start a DynamoDB Local instance on port 8000. The data will be persisted in the `dynamodb-data` directory at the project root.

### 2. Initialize Database Tables

The first time you run the application, the database tables will be automatically created. You can also manually initialize the tables:

```bash
# Run the database initialization script
python -m src.database.init_db
```

### 3. Seed Test Data

If you want to populate the database with sample data for development:

```bash
# Run the seed script
./scripts/seed_data.py
```

## Interacting with DynamoDB Local

### Using the Application

The application is configured to connect to DynamoDB Local when the `ENVIRONMENT` environment variable is set to `development` (default).

### Using AWS CLI

You can interact with DynamoDB Local using the AWS CLI:

```bash
# List tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Scan a table
aws dynamodb scan --table-name Players --endpoint-url http://localhost:8000
```

### Using DynamoDB Admin UI (Optional)

For a graphical interface, you can install and use dynamodb-admin:

```bash
# Install dynamodb-admin
npm install -g dynamodb-admin

# Run dynamodb-admin
DYNAMO_ENDPOINT=http://localhost:8000 dynamodb-admin
```

Then open http://localhost:8001 in your browser.

## Data Persistence

DynamoDB Local data is persisted in the `dynamodb-data` directory. This means:

- Data will be preserved between container restarts
- You can stop and start the container without losing data
- To reset the database, stop the container and delete the `dynamodb-data` directory

## Switching to Production DynamoDB

When deploying to production, set the `ENVIRONMENT` environment variable to `production`. This will make the application connect to AWS DynamoDB instead of the local instance.

You'll need to set up the following environment variables for production:

- `AWS_REGION`: The AWS region where your DynamoDB tables are located
- AWS credentials (either through environment variables or AWS configuration files)

## Docker Compose Configuration

The Docker Compose configuration for DynamoDB Local is in `docker/dev/docker-compose.yml`. The key settings are:

- Port mapping: `8000:8000`
- Data directory: `../../dynamodb-data:/home/dynamodblocal/data`
- Shared database mode: `-sharedDb`

## Troubleshooting

### Connection Issues

If you can't connect to DynamoDB Local:

1. Ensure the container is running: `docker ps | grep dynamodb-local`
2. Check the container logs: `docker logs dynamodb-local`
3. Verify the port mapping: `docker-compose ps`

### Data Issues

If you're experiencing data issues:

1. Check the table structure: `aws dynamodb describe-table --table-name Players --endpoint-url http://localhost:8000`
2. Scan the table to see its contents: `aws dynamodb scan --table-name Players --endpoint-url http://localhost:8000`
3. Consider resetting the database by removing the `dynamodb-data` directory and restarting the container
