# Tennis Meetup Bot

A Discord bot designed to manage a tennis community server, handling new member onboarding, NTRP ratings, court preferences, and role management.

## Features

### Server Setup

- `/admin setup roles` - Sets up server roles:

  - Court Visitor (default role for new members)
  - Club Member (active members who have completed profile setup)
  - Tennis Bot (bot role with necessary permissions)

- `/admin setup channels` - Creates and configures channels:

  - #welcome-and-rules (in Information category)
  - #court-side (in General category)
  - Channel permissions are automatically set based on roles

- `/admin courts` - Manages tennis court data:
  - `load` - Load court data from configuration
  - `list` - View all registered courts

### Member Management

- **New Member Onboarding**:

  - Automatically assigns "Court Visitor" role to new members
  - Sends welcome message in #welcome-and-rules
  - Prompts new members to use `/get-started` command
  - Only the new member can interact with their profile setup buttons

- **Profile System**:

  - **NTRP Rating System**:

    - Option to input known NTRP rating
    - Guided questionnaire for rating calculation
    - 2-week calibration period for new ratings
    - Rating adjustments with cooldown periods

  - **Player Preferences**:

    - Tennis interests selection
    - Preferred court locations
    - Profile information stored in DynamoDB

  - **Commands**:

    - `/get-started` - Complete profile setup
    - `/view-profile` - Check current profile
    - `/update-profile` - Modify profile settings

  - Automatic role upgrade to "Club Member" after profile setup

### NTRP Rating Categories

- Beginner (1.0-2.0)
- Advanced Beginner (2.0-3.0)
- Intermediate (3.0-4.0)
- Advanced Intermediate (4.0-5.0)
- Advanced (5.0+)

### Configuration

- Server settings in `guild_config.yaml`
- NTRP configuration in `ntrp_config.yaml`
- Role permissions in `permissions.py`
- Test guild ID in `constants.py`
- DynamoDB configuration in `dynamodb_config.py`

### Database Models

- **Player Model**:

  - Basic info (ID, username)
  - NTRP rating and calculation data
  - Interests and preferred locations
  - Calibration period tracking
  - Rating update history

- **Court Model**:

  - Location and facilities info
  - Surface type and number of courts
  - Amenities and booking details
  - Google Maps integration

- **Schedule Model**:
  - Player availability
  - Start and end times
  - Recurrence patterns
  - Location preferences
  - Skill level preferences

## Prerequisites

### Required Software

- Python 3.13.2
- Docker and Docker Compose
  - Download from: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
  - Required for running DynamoDB Local
- AWS CLI
  - Install with: `pip install awscli`
  - Used for interacting with DynamoDB Local directly
- Virutal Environment
  - `conda create -n <environment_name> python=<version>`
  - `conda activate <environment_name>`

### File Setup
`chmod +x dynamodb-data/shared-local-instance.db`

### Python Dependencies

```
pip install -r requirements.txt
```

Key dependencies:

- nextcord==3.0.1 (Discord API)
- boto3==1.34.0 (AWS SDK for DynamoDB)
- dateparser==1.2.0 (Natural language date parsing)
- python-dotenv==1.0.1 (Environment variable management)

## Local Development Setup

### 1. Environment Variables

Create a `.env` file in the project root with:

```
DISCORD_TOKEN=your_discord_bot_token
ENVIRONMENT=development
```

### 2. Start DynamoDB Local

#### Docker Setup

**Start Docker Desktop**

- On macOS: Open Docker Desktop from Applications folder or use Spotlight (Cmd+Space)

```bash
# Navigate to the dev directory
cd docker/dev

# Start DynamoDB Local
docker-compose up -d dynamodb-local
```

### 3. Initialize Database Tables

```bash
# Run the database initialization script
python -m src.database.init_db
```

### 4. Seed Test Data (Optional)

```bash
# Run the seed script to populate test data
chmod +x ./scripts/seed_data.py
python ./scripts/seed_data.py
```

### 5. Run the Bot

```bash
python dev.py
```

## DynamoDB Local Tools

### Using AWS CLI with DynamoDB Local

```bash
# List tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Scan a table
aws dynamodb scan --table-name Players --endpoint-url http://localhost:8000
```

### Using DynamoDB Admin UI (Optional)

For a graphical interface to view and manage your DynamoDB data:

```bash
# Install dynamodb-admin
npm install -g dynamodb-admin

# Run dynamodb-admin
DYNAMO_ENDPOINT=http://localhost:8000 dynamodb-admin
```

Then open http://localhost:8001 in your browser.

## Next Steps

1. Implement match scheduling system
2. Develop player matching algorithm based on:
   - NTRP ratings
   - Preferred locations
   - Availability patterns
3. Create admin dashboard for:
   - Player rating management
   - Court administration
   - Match/event coordination
4. Add rating verification system
5. Implement automated tournaments
6. Develop coaching session management
7. Add player statistics and history
8. Create court reservation system
9. Implement rating adjustments based on match results

## AWS Deployment

For detailed instructions on deploying to AWS with DynamoDB, see [README-DYNAMODB.md](README-DYNAMODB.md).
