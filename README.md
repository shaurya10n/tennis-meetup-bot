# Tennis Meetup Bot

A Discord bot for managing a tennis community server, handling onboarding, NTRP ratings, court preferences, match scheduling, and more. Built for extensibility and robust community management.

---

## Table of Contents

- [Features](#features)
- [Command Reference](#command-reference)
- [Architecture Overview](#architecture-overview)
- [Database Models](#database-models)
- [Setup & Installation](#setup--installation)
- [Local Development](#local-development)
- [Deployment & Update Workflow](#deployment--update-workflow)
- [Advanced Features](#advanced-features)
- [Next Steps](#next-steps)
- [AWS Deployment](#aws-deployment)
- [Contributing](#contributing)

---

## Features

- **Automated onboarding**: Assigns roles, sends welcome messages, and guides new members through profile setup.
- **NTRP Rating System**: Supports both self-reported and questionnaire-based ratings, with calibration and adjustment periods.
- **Player Preferences**: Collects and manages interests, preferred locations, and skill/gender preferences.
- **Court Management**: Admins can add, update, and list courts with location, surface, amenities, and Google Maps links.
- **Schedule Management**: Natural language parser for adding/viewing/clearing availability (e.g., "next Monday 4-6pm").
- **Player Matching**: Advanced algorithm considers NTRP, preferences, time/location overlap, engagement, and match history.
- **Match Management**: Schedule, complete, and view matches; record results and update ratings.
- **Admin Dashboard**: Visualize player availability and currently playing users by location and time slot.
- **User Engagement Tracking**: Tracks activity (messages, matches, etc.) for improved matchmaking and analytics.

---

## Command Reference

### User Commands

- `/get-started` — Begin profile setup (step-by-step, only for new users)
- `/view-profile` — View your tennis profile
- `/update-profile` — Update NTRP, preferences, locations, etc.
- `/schedule add <when>` — Add your availability (e.g., "today 4-6pm")
- `/schedule view [filter]` — View your schedule (filters: today, this week, etc.)
- `/schedule clear <period>` — Clear your schedule for a period
- `/find-matches [hours_ahead]` — Find potential matches (default: next 7 days)
- `/find-matches-for-schedule <schedule_id>` — Find matches for a specific schedule
- `/matches-view <type>` — View your completed or upcoming matches
- `/complete-match` — Complete a scheduled match and record results
- `/matches complete <match_id>` — Complete a match by ID

### Admin Commands

- `/admin setup roles` — Set up server roles
- `/admin setup channels` — Set up server channels
- `/admin courts load` — Load court data from config
- `/admin courts list` — List all registered courts
- `/admin dashboard view [location]` — View the availability dashboard
- `/admin dashboard playing` — View currently playing users

---

## Architecture Overview

- **Bot Framework**: [nextcord](https://github.com/nextcord/nextcord) (Discord API)
- **Database**: DynamoDB (local for dev, AWS for prod)
- **Dockerized**: For local and cloud deployment, including DynamoDB Local
- **Modular Cogs**: User, admin, dashboard, and command groups
- **Natural Language Parsing**: For schedule input (see [Schedule Parser](#schedule-parser))
- **Matching Algorithm**: Multi-factor, extensible (see [Matching Algorithm](#matching-algorithm))

---

## Database Models

- **Player**: ID, username, NTRP, preferences, interests, locations, engagement, history
- **Court**: Name, location, surface, amenities, Google Maps link
- **Schedule**: Player, time range, recurrence, location, preferences
- **Match**: Players, time, court, status, results, quality score
- **User Engagement**: Activity type, value, timestamp, details

---

## Setup & Installation

### Prerequisites

- Python 3.13.2
- Docker & Docker Compose ([Download](https://www.docker.com/products/docker-desktop/))
- AWS CLI (`pip install awscli`)
- Virtual Environment (recommended: conda)

### File Setup

- Ensure `dynamodb-data/shared-local-instance.db` is executable:
  ```sh
  chmod +x dynamodb-data/shared-local-instance.db
  ```
- Install Python dependencies:
  ```sh
  pip install -r requirements.txt
  ```

### Environment Variables

Create a `.env` file in the project root:

```
DISCORD_TOKEN=your_discord_bot_token
ENVIRONMENT=development
```

---

## Local Development

1. **Start Docker Desktop** (macOS: Applications or Spotlight)
2. **Start DynamoDB Local**
   ```sh
   cd docker/dev
   docker-compose up -d dynamodb-local
   ```
3. **Initialize Database Tables**
   ```sh
   python -m src.database.init_db
   ```
4. **Seed Test Data (Optional)**
   ```sh
   chmod +x ./scripts/seed_data.py
   python ./scripts/seed_data.py
   ```
5. **Run the Bot**
   ```sh
   python main.py
   ```

---

## Deployment & Update Workflow

### Running on EC2 (Docker Compose)

- Both the bot and DynamoDB Local run as containers on a shared network.
- See [README-DYNAMODB.md](README-DYNAMODB.md) for AWS-specific details.

#### Initial Setup

1. Copy project files to EC2:
   ```sh
   scp -i <your-key.pem> -r /path/to/tennis-meetup-bot/* ubuntu@<EC2-IP>:/home/ubuntu/Tennis_Bot/
   ```
2. SSH into EC2:
   ```sh
   ssh -i <your-key.pem> ubuntu@<EC2-IP>
   cd /home/ubuntu/Tennis_Bot/
   ```
3. Ensure `.env` is present.
4. Start the stack:
   ```sh
   docker-compose up -d
   ```
5. Seed DynamoDB:
   ```sh
   docker-compose exec bot python3 scripts/seed_data.py
   ```

#### Updating the Bot

- **Production (ECR):**
  - Build and push Docker image, then pull and restart on EC2.
- **Dev:**
  - Copy code, rebuild, and restart container on EC2.

#### Debugging

- View logs:
  ```sh
  docker-compose logs -f bot
  ```
- If you see `ResourceNotFoundException`, re-seed the database.

---

## Advanced Features

### Matching Algorithm

- Considers NTRP, skill/gender/location preferences, time overlap, engagement, and match history.
- Supports singles and doubles suggestions.
- Configurable weights for each factor.
- See `src/utils/matching_algorithm.py` and [docs/matching_algorithm.md](docs/matching_algorithm.md).

### Schedule Parser

- Accepts natural language ("next Monday 4-6pm", "every Thursday afternoon").
- Fuzzy correction for typos and abbreviations.
- Handles recurrence, time ranges, and special cases.
- See `src/cogs/user/commands/schedule/parser/nlp_parser.py` and [docs/matching_integration.md](docs/matching_integration.md).

### Admin Dashboard

- Visualizes player availability by location and time slot for the next 7 days.
- Shows currently playing users.
- Interactive navigation and refresh.

### Court Management

- Courts can be added, updated, listed, and filtered by location or attribute.
- Each court includes name, location, surface, amenities, and Google Maps link.

### User Engagement Tracking

- Tracks activity (messages, matches, etc.) for each user.
- Used to boost matchmaking for active members.
- See `src/database/dao/dynamodb/user_engagement_dao.py`.

---

## Next Steps

- Implement automated tournaments
- Add rating verification system
- Expand admin dashboard (stats, heatmaps)
- Add coaching session management
- Player statistics/history UI
- Court reservation system
- More advanced rating adjustments

---

## AWS Deployment

See [README-DYNAMODB.md](README-DYNAMODB.md) for full AWS deployment instructions.

---

## Contributing

- PRs and issues welcome!
- See `docs/` for architecture and algorithm details.
- Please update this README if you add new features or commands.
