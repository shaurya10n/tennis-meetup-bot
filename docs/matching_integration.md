# Matching Algorithm Integration Guide

## Overview

This guide explains how to integrate the new tennis player matching algorithm into your existing Discord bot. The matching system provides intelligent match suggestions based on NTRP ratings, skill preferences, gender preferences, time availability, and location preferences.

## What's Been Added

### 1. New Database Models

#### Match Model (`src/database/models/dynamodb/match.py`)

- Stores match information including players, times, courts, and results
- Supports both singles and doubles matches
- Tracks match status (scheduled, in_progress, completed, cancelled)
- Stores player ratings and match quality scores

#### Match DAO (`src/database/dao/dynamodb/match_dao.py`)

- Handles all database operations for matches
- Provides methods for creating, updating, and querying matches
- Supports filtering by status, court, and time ranges

### 2. Matching Algorithm (`src/utils/matching_algorithm.py`)

- Core algorithm that finds optimal matches between players
- Multi-factor compatibility scoring system
- Supports both singles and doubles match generation
- Configurable weights and thresholds

### 3. Discord Commands

#### Find Matches Command (`src/cogs/user/commands/find_matches/`)

- `/find-matches [hours_ahead]` - Find matches in the next N hours
- `/find-matches-for-schedule <schedule_id>` - Find matches for a specific schedule
- Interactive UI with accept/decline buttons
- Detailed match information and compatibility breakdown

## Integration Steps

### Step 1: Update Database Schema

The new Match table will be automatically created when you run the database initialization:

```python
# This is already updated in src/database/init_db.py
from src.database.models.dynamodb import Player, Schedule, Court, UserEngagement, Match

def init_database():
    # ... existing code ...
    if Match.TABLE_NAME not in existing_tables:
        print(f"Creating {Match.TABLE_NAME} table...")
        Match.create_table(dynamodb)
```

### Step 2: Add Commands to Your Bot

Add the new commands to your main bot file:

```python
# In your main bot file (e.g., main.py)
from src.cogs.user.commands.find_matches import find_matches_command, find_matches_for_schedule_command

# Add the commands to your bot
@bot.slash_command(name="find-matches", description="Find potential tennis matches")
async def find_matches(interaction: nextcord.Interaction, hours_ahead: int = 168):
    await find_matches_command(interaction, hours_ahead)

@bot.slash_command(name="find-matches-for-schedule", description="Find matches for a specific schedule")
async def find_matches_for_schedule(interaction: nextcord.Interaction, schedule_id: str):
    await find_matches_for_schedule_command(interaction, schedule_id)
```

### Step 3: Update Schedule Model

The existing Schedule model already has a `match_id` field, so no changes are needed. When a match is created, the schedules will be updated to reference the match.

### Step 4: Test the Integration

Run the test script to verify everything works:

```bash
cd tests
python test_matching_algorithm.py
```

## Usage Examples

### For Users

1. **Complete Profile Setup**

   ```
   /get-started
   ```

   - Set NTRP rating
   - Choose skill level preferences
   - Set gender preferences
   - Select preferred locations

2. **Add Availability**

   ```
   /schedule add "tomorrow 4-6pm"
   ```

3. **Find Matches**

   ```
   /find-matches 72
   ```

   - Finds matches in the next 72 hours
   - Shows interactive suggestions
   - Accept or decline matches

4. **Find Matches for Specific Schedule**
   ```
   /find-matches-for-schedule <schedule_id>
   ```

### For Developers

#### Using the Matching Algorithm Directly

```python
from src.utils.matching_algorithm import TennisMatchingAlgorithm
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.config.dynamodb_config import get_db

# Initialize
db = get_db()
player_dao = PlayerDAO(db)
schedule_dao = ScheduleDAO(db)
court_dao = CourtDAO(db)
match_dao = MatchDAO(db)

algorithm = TennisMatchingAlgorithm(player_dao, schedule_dao, court_dao, match_dao)

# Find matches
suggestions = algorithm.find_matches_for_player(
    guild_id="your-guild-id",
    user_id="user-id",
    hours_ahead=168  # 1 week
)

# Process suggestions
for suggestion in suggestions:
    print(f"Match: {suggestion.players[0].username} vs {suggestion.players[1].username}")
    print(f"Score: {suggestion.overall_score}")
    print(f"Reasons: {suggestion.reasons}")
```

#### Creating Matches Programmatically

```python
# Create a match from a suggestion
match = match_dao.create_match(
    guild_id="guild-id",
    schedule_id=suggestion.schedules[0].schedule_id,
    court_id=suggestion.suggested_court.court_id,
    start_time=suggestion.suggested_time[0],
    end_time=suggestion.suggested_time[1],
    players=[p.user_id for p in suggestion.players],
    match_type=suggestion.match_type,
    status="scheduled",
    player_ratings={p.user_id: p.ntrp_rating for p in suggestion.players}
)

# Update schedules to reference the match
for schedule in suggestion.schedules:
    schedule_dao.update_schedule(
        guild_id="guild-id",
        schedule_id=schedule.schedule_id,
        match_id=match.match_id,
        status="matched"
    )
```

## Configuration Options

### Algorithm Weights

You can adjust the importance of different factors by modifying the weights in `TennisMatchingAlgorithm`:

```python
self.weights = {
    'ntrp_compatibility': 0.25,    # NTRP rating similarity
    'skill_preference': 0.20,      # Skill level preferences
    'gender_compatibility': 0.15,  # Gender preferences
    'location_compatibility': 0.15, # Location preferences
    'time_overlap': 0.15,          # Time availability
    'engagement_bonus': 0.05,      # Player engagement
    'match_history': 0.05          # Previous match quality
}
```

### NTRP Thresholds

Adjust the NTRP compatibility thresholds:

```python
self.ntrp_thresholds = {
    'excellent': 0.5,  # Within 0.5 rating
    'good': 1.0,       # Within 1.0 rating
    'acceptable': 1.5,  # Within 1.5 rating
    'poor': 2.0        # Within 2.0 rating
}
```

### Score Thresholds

Set minimum scores for match suggestions:

```python
score_thresholds = {
    'minimum_singles': 0.3,   # Minimum score for singles matches
    'minimum_doubles': 0.25,  # Minimum score for doubles matches
    'excellent': 0.8,         # Excellent match threshold
    'good': 0.6               # Good match threshold
}
```

## Monitoring and Analytics

### Key Metrics to Track

1. **Match Success Rate**: Percentage of suggested matches that are accepted
2. **Average Compatibility Score**: Overall quality of matches
3. **Response Time**: How long it takes to find matches
4. **User Satisfaction**: Post-match quality ratings

### Logging

The algorithm includes comprehensive logging:

```python
logger.info(f"Found {len(suggestions)} matches for player {user_id}")
logger.debug(f"Compatibility scores: {compatibility_details}")
logger.warning(f"Low match quality: {overall_score}")
```

## Troubleshooting

### Common Issues

1. **No Matches Found**

   - Check if players have overlapping schedules
   - Verify player preferences are set
   - Ensure players have compatible NTRP ratings

2. **Database Errors**

   - Run database initialization: `python -c "from src.database.init_db import init_database; init_database()"`
   - Check DynamoDB permissions
   - Verify table names and schemas

3. **Performance Issues**
   - Limit time ranges for queries
   - Use pagination for large result sets
   - Consider caching frequently accessed data

### Debug Mode

Enable debug logging to see detailed algorithm information:

```python
import logging
logging.getLogger('src.utils.matching_algorithm').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Automatic Match Notifications**: Notify players when good matches are available
2. **Match Quality Learning**: Use match results to improve future suggestions
3. **Tournament Support**: Generate tournament brackets and schedules
4. **Weather Integration**: Consider weather for outdoor court matches
5. **Transportation**: Factor in travel time between locations

### Algorithm Improvements

1. **Machine Learning**: Use ML to predict match quality
2. **Dynamic Weights**: Adjust weights based on user feedback
3. **Fairness Metrics**: Ensure equitable match distribution
4. **Social Network Analysis**: Consider player relationships

## Support

For questions or issues with the matching algorithm:

1. Check the documentation in `docs/matching_algorithm.md`
2. Run the test script: `python tests/test_matching_algorithm.py`
3. Review the logs for error messages
4. Check the database schema and data integrity

The matching algorithm is designed to be robust, scalable, and continuously improvable. Regular monitoring and user feedback will help optimize the system for your specific community needs.
