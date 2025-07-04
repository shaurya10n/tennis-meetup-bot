# Tennis Player Matching Algorithm

## Overview

The Tennis Player Matching Algorithm is a sophisticated system that finds optimal tennis matches between players based on multiple compatibility factors. It considers NTRP ratings, skill level preferences, gender preferences, time availability, location preferences, and match history to create the best possible matches.

## Key Features

### 1. Multi-Factor Compatibility Scoring

The algorithm evaluates matches using a weighted scoring system:

- **NTRP Rating Compatibility (25%)**: Matches players with similar skill levels
- **Skill Level Preferences (20%)**: Respects player preferences for opponent skill levels
- **Gender Compatibility (15%)**: Considers gender preferences for matches
- **Location Compatibility (15%)**: Matches players who prefer the same courts
- **Time Overlap (15%)**: Ensures players are available at the same time
- **Engagement Bonus (5%)**: Rewards active players
- **Match History (5%)**: Considers previous match quality ratings

### 2. NTRP Rating Compatibility

The algorithm uses the National Tennis Rating Program (NTRP) to match players:

- **Excellent Match**: Within 0.5 NTRP rating (score: 1.0)
- **Good Match**: Within 1.0 NTRP rating (score: 0.8)
- **Acceptable Match**: Within 1.5 NTRP rating (score: 0.6)
- **Poor Match**: Within 2.0 NTRP rating (score: 0.3)
- **No Match**: Beyond 2.0 NTRP rating (score: 0.0)

### 3. Skill Level Preferences

Players can specify their preferred opponent skill levels:

- **Similar Level**: ±0.5 NTRP rating
- **Above Level**: +1.0 NTRP rating
- **Below Level**: -1.0 NTRP rating
- **Any Level**: No preference

### 4. Gender Compatibility

The system respects gender preferences:

- **No Preference**: Compatible with any gender
- **Specific Gender**: Only matches with preferred gender
- **Partial Match**: Rewards when preferences align

### 5. Location Matching

Matches players who prefer the same courts:

- **Perfect Match**: Same preferred locations (score: 1.0)
- **Partial Match**: One player has no preference (score: 0.5)
- **No Match**: Different location preferences (score: 0.0)

### 6. Time Overlap Calculation

Calculates the percentage of time overlap between schedules:

```
overlap_score = overlap_duration / min(schedule1_duration, schedule2_duration)
```

### 7. Engagement Bonus

Rewards players with high engagement scores:

- Based on message activity, match participation, and overall engagement
- Normalized to 0-1 scale
- Encourages active community participation

### 8. Match History Factor

Considers previous match quality:

- **High Quality**: Previous match rated >7/10 (score: 1.0)
- **Good Quality**: Previous match rated >5/10 (score: 0.5)
- **No History**: No previous matches (score: 0.0)

## Algorithm Flow

### 1. Player Discovery

```python
# Find all available schedules in time range
available_schedules = get_schedules_in_time_range(start_time, end_time)

# Get all players for available schedules
all_players = get_players_for_schedules(guild_id, available_schedules)
```

### 2. Schedule Grouping

```python
# Group schedules by time overlap
overlapping_groups = group_schedules_by_overlap(player_schedule, available_schedules)
```

### 3. Match Generation

#### Singles Matches (2 players)

- Find all compatible players for each schedule
- Calculate pairwise compatibility scores
- Filter by minimum threshold (0.3)
- Sort by overall score

#### Doubles Matches (4 players)

- Find groups of 4 compatible players
- Calculate group compatibility (average of all pairwise scores)
- Filter by minimum threshold (0.25)
- Sort by overall score

### 4. Court Assignment

```python
# Find best court based on player preferences
suggested_court = find_best_court(player1, player2, schedule1, schedule2)

# Priority: Common locations > Any available court > None
```

### 5. Time Optimization

```python
# Find optimal match time within overlapping schedules
match_start, match_end = find_optimal_match_time(schedule1, schedule2)

# Default: 90 minutes with 15-minute warm-up
```

## Usage Examples

### Basic Match Finding

```python
# Find matches for a player in the next week
suggestions = matching_algorithm.find_matches_for_player(
    guild_id="123456789",
    user_id="987654321",
    hours_ahead=168  # 1 week
)
```

### Schedule-Specific Matching

```python
# Find matches for a specific schedule
suggestions = matching_algorithm.find_matches_for_schedule(
    guild_id="123456789",
    schedule_id="schedule-uuid"
)
```

### Discord Command Integration

```python
# /find-matches command
await find_matches_command(interaction, hours_ahead=72)  # 3 days

# /find-matches-for-schedule command
await find_matches_for_schedule_command(interaction, schedule_id="uuid")
```

## Configuration

### Weights Configuration

```python
weights = {
    'ntrp_compatibility': 0.25,
    'skill_preference': 0.20,
    'gender_compatibility': 0.15,
    'location_compatibility': 0.15,
    'time_overlap': 0.15,
    'engagement_bonus': 0.05,
    'match_history': 0.05
}
```

### NTRP Thresholds

```python
ntrp_thresholds = {
    'excellent': 0.5,  # Within 0.5 rating
    'good': 1.0,       # Within 1.0 rating
    'acceptable': 1.5,  # Within 1.5 rating
    'poor': 2.0        # Within 2.0 rating
}
```

### Score Thresholds

```python
score_thresholds = {
    'minimum_singles': 0.3,
    'minimum_doubles': 0.25,
    'excellent': 0.8,
    'good': 0.6
}
```

## Match Suggestion Structure

```python
@dataclass
class MatchSuggestion:
    players: List[Player]           # List of players in the match
    schedules: List[Schedule]       # Associated schedules
    suggested_court: Optional[Court] # Recommended court
    suggested_time: Tuple[int, int] # (start_time, end_time)
    overall_score: float           # Overall compatibility score
    match_type: str                # "singles" or "doubles"
    compatibility_details: Dict[str, float]  # Detailed scores
    reasons: List[str]             # Human-readable reasons
```

## Database Schema

### Matches Table

```sql
CREATE TABLE Matches (
    guild_id STRING,           -- Partition key
    match_id STRING,           -- Sort key
    schedule_id STRING,        -- Reference to primary schedule
    court_id STRING,           -- Assigned court
    start_time NUMBER,         -- Match start time (Unix timestamp)
    end_time NUMBER,           -- Match end time (Unix timestamp)
    players LIST<STRING>,      -- List of player user IDs
    match_type STRING,         -- "singles" or "doubles"
    status STRING,             -- "scheduled", "in_progress", "completed", "cancelled"
    score MAP,                 -- Match score details
    winner STRING,             -- Winner user ID
    match_quality_score DECIMAL, -- Player rating of match quality
    player_ratings MAP,        -- NTRP ratings at time of match
    created_at STRING,         -- ISO timestamp
    updated_at STRING,         -- ISO timestamp
    cancelled_reason STRING,   -- Reason for cancellation
    notes STRING               -- Additional notes
);
```

## Performance Considerations

### Optimization Strategies

1. **Indexed Queries**: Use GSI on start_time for efficient time-based queries
2. **Batch Processing**: Process multiple schedules in batches
3. **Caching**: Cache player data and preferences
4. **Lazy Loading**: Load detailed information only when needed

### Scalability

- **Horizontal Scaling**: Algorithm works with multiple guilds independently
- **Time-based Partitioning**: Queries limited to specific time ranges
- **Result Limiting**: Return top N suggestions to avoid overwhelming users

## Future Enhancements

### Planned Features

1. **Machine Learning**: Use ML to improve match quality predictions
2. **Dynamic Weights**: Adjust weights based on user feedback
3. **Advanced Scheduling**: Support for tournament-style matches
4. **Weather Integration**: Consider weather conditions for outdoor courts
5. **Transportation**: Factor in travel time between locations

### Algorithm Improvements

1. **Multi-objective Optimization**: Balance multiple conflicting preferences
2. **Fairness Metrics**: Ensure equitable match distribution
3. **Learning from Outcomes**: Use match results to improve future matches
4. **Social Network Analysis**: Consider player relationships and history

## Testing

### Unit Tests

```python
def test_ntrp_compatibility():
    algorithm = TennisMatchingAlgorithm(...)
    score = algorithm._calculate_ntrp_compatibility(0.3)
    assert score == 1.0  # Excellent match

def test_skill_preference_compatibility():
    # Test various skill preference combinations
    pass

def test_gender_compatibility():
    # Test gender preference matching
    pass
```

### Integration Tests

```python
def test_end_to_end_matching():
    # Test complete matching flow
    pass

def test_match_creation():
    # Test match creation and database updates
    pass
```

## Monitoring and Analytics

### Key Metrics

- **Match Success Rate**: Percentage of accepted matches
- **Average Compatibility Score**: Overall match quality
- **Response Time**: Time to find matches
- **User Satisfaction**: Post-match ratings

### Logging

```python
logger.info(f"Found {len(suggestions)} matches for player {user_id}")
logger.debug(f"Compatibility scores: {compatibility_details}")
logger.warning(f"Low match quality: {overall_score}")
```

## Conclusion

The Tennis Player Matching Algorithm provides a comprehensive solution for finding optimal tennis matches. By considering multiple factors and using a sophisticated scoring system, it ensures that players are matched with compatible opponents at convenient times and locations. The algorithm is designed to be scalable, configurable, and continuously improvable based on user feedback and match outcomes.
