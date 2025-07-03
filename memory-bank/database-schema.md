# Database Schema Documentation

This document provides a comprehensive overview of the database structure for the Tennis Meetup user_id Bot. It is designed to be easily understood by both humans and LLMs.

## Entity Relationship Diagram

```mermaid
erDiagram
    Players ||--o{ Schedules : "creates"
    Players ||--o{ UserEngagement : "generates"
    Courts ||--o{ Schedules : "hosts"

    Players {
        string guild_id PK "user_id server ID"
        string user_id_id PK "user_id user ID"
        string username "user_id username"
        string dob "Date of birth (MM/DD/YYYY)"
        string gender "Player's gender"
        decimal ntrp_rating "NTRP rating (2.0-5.0)"
        boolean knows_ntrp "Whether player knows their NTRP rating"
        list interests "Tennis interests"
        map preferences "Contains locations, skill_levels, gender"
        list roles "user_id roles with ID and name"
        decimal rating "Algorithm-based rating (future)"
        map rating_responses "Responses to NTRP assessment"
        string calibration_ends_at "ISO timestamp with UTC timezone"
        string last_rating_update "ISO timestamp with UTC timezone"
        string created_at "ISO timestamp with UTC timezone"
        string updated_at "ISO timestamp with UTC timezone"
        decimal engagement_score "Overall engagement metric"
        string last_active "ISO timestamp with UTC timezone"
        map engagement_summary "Engagement metrics summary"
    }

    Courts {
        string court_id PK "Unique court identifier"
        string name "Court name"
        string location GSI "Location name"
        string surface_type "Court surface type"
        int number_of_courts "Number of courts at location"
        boolean is_indoor "Whether courts are indoor"
        list amenities "Available amenities"
        string google_maps_link "Google Maps URL"
        string description "Optional description"
        decimal cost_per_hour "Optional cost information"
        string booking_url "Optional booking URL"
        string created_at "ISO timestamp with UTC timezone"
        string updated_at "ISO timestamp with UTC timezone"
    }

    Schedules {
        string guild_id PK "user_id server ID"
        string schedule_id SK "Unique schedule identifier"
        string user_id "user_id user ID"
        int start_time GSI "Start time as Unix timestamp"
        int end_time "End time as Unix timestamp"
        string parent_schedule_id GSI "ID of parent recurring schedule (if instance)"
        map recurrence "Recurrence pattern (only on parent schedules)"
        map preference_overrides "Overrides for player preferences"
        string status "Schedule status (open, closed, cancelled, completed)"
        string match_id "Reference to match record (optional)"
        string created_at "ISO timestamp with UTC timezone"
        string updated_at "ISO timestamp with UTC timezone"
        string timezone "Timezone string (e.g., America/Vancouver)"
    }

    UserEngagement {
        string guild_id PK "user_id server ID"
        string engagement_id PK "Unique engagement identifier"
        string user_id GSI "user_id user ID"
        string timestamp GSI "ISO timestamp with UTC timezone"
        string activity_type GSI "Type of activity (e.g., message, match)"
        map details "Additional details about the engagement"
        decimal engagement_value "Value of the engagement for scoring"
    }
```

## Table Schemas

### Players Table

| Attribute | Type | Description | Key Type |
|-----------|------|-------------|----------|
| guild_id | String | user_id server ID | Partition Key |
| user_id_id | String | user_id user ID | Sort Key |
| username | String | Player's user_id username | |
| dob | String | Date of birth (MM/DD/YYYY) | |
| gender | String | Player's gender | |
| ntrp_rating | Decimal | National Tennis Rating Program rating (2.0-5.0) | |
| knows_ntrp | Boolean | Whether player knows their NTRP rating | |
| interests | List[String] | Tennis interests | |
| preferences | Map | Contains locations, skill_levels, gender preferences | |
| roles | List[Map] | user_id roles with role_id and role_name | |
| rating | Decimal | Algorithm-based rating (future) | |
| rating_responses | Map | Responses to NTRP assessment questions | |
| calibration_ends_at | String | ISO timestamp when rating calibration ends | |
| last_rating_update | String | ISO timestamp of last rating update | |
| created_at | String | ISO timestamp of creation | |
| updated_at | String | ISO timestamp of last update | |
| engagement_score | Decimal | Overall engagement metric | |
| last_active | String | ISO timestamp of last activity | |
| engagement_summary | Map | Summary of engagement metrics | |

### Courts Table

| Attribute | Type | Description | Key Type |
|-----------|------|-------------|----------|
| court_id | String | Unique court identifier | Partition Key |
| name | String | Court name | |
| location | String | Location name | GSI Partition Key |
| surface_type | String | Court surface type | |
| number_of_courts | Number | Number of courts at location | |
| is_indoor | Boolean | Whether courts are indoor | |
| amenities | List[String] | Available amenities | |
| google_maps_link | String | Google Maps URL | |
| description | String | Optional description | |
| cost_per_hour | Decimal | Optional cost information | |
| booking_url | String | Optional booking URL | |
| created_at | String | ISO timestamp of creation | |
| updated_at | String | ISO timestamp of last update | |

### Schedules Table

| Attribute | Type | Description | Key Type |
|-----------|------|-------------|----------|
| guild_id | String | user_id server ID | Partition Key |
| schedule_id | String | Unique schedule identifier | Sort Key |
| user_id | String | user_id user ID | |
| start_time | Number | Start time as Unix timestamp | GSI Partition Key |
| end_time | Number | End time as Unix timestamp | |
| parent_schedule_id | String | ID of parent recurring schedule (if instance) | GSI Partition Key |
| recurrence | Map | Recurrence pattern (only on parent schedules) | |
| preference_overrides | Map | Overrides for player preferences | |
| status | String | Schedule status (open, closed, cancelled, completed) | |
| match_id | String | Reference to match record (optional) | |
| created_at | String | ISO timestamp of creation | |
| updated_at | String | ISO timestamp of last update | |
| timezone | String | Timezone string (e.g., America/Vancouver) | |

### UserEngagement Table

| Attribute | Type | Description | Key Type |
|-----------|------|-------------|----------|
| guild_id | String | user_id server ID | Partition Key |
| engagement_id | String | Unique engagement identifier | Sort Key |
| user_id | String | user_id user ID | GSI Partition Key |
| timestamp | String | ISO timestamp with UTC timezone | GSI Sort Key |
| activity_type | String | Type of activity (e.g., message, match) | GSI Partition Key |
| details | Map | Additional details about the engagement | |
| engagement_value | Decimal | Value of the engagement for scoring | |

## Global Secondary Indexes (GSIs)

### Schedules Table
- **UserSchedulesIndex**: Allows querying schedules by user
  - Partition Key: `user_id`
  - Sort Key: `start_time`
  - Projection: ALL
- **StartTimeIndex**: Allows querying schedules by start time
  - Partition Key: `start_time`
  - Projection: ALL
- **RecurringInstancesIndex**: Allows querying instances of a recurring schedule
  - Partition Key: `parent_schedule_id`
  - Sort Key: `start_time`
  - Projection: ALL

### Courts Table
- **LocationIndex**: Allows querying courts by location
  - Partition Key: `location`
  - Projection: ALL

### UserEngagement Table
- **UserIndex**: Allows querying engagements by user
  - Partition Key: `user_id`
  - Sort Key: `timestamp`
  - Projection: ALL
- **ActivityTypeIndex**: Allows querying engagements by activity type
  - Partition Key: `activity_type`
  - Sort Key: `timestamp`
  - Projection: ALL

## Recurring Schedule Implementation

The system implements recurring schedules using a materialized instances approach:

1. **Parent Schedule**: When a user creates a recurring schedule, a parent schedule record is created with:
   - A unique `schedule_id`
   - The `recurrence` field containing the pattern details
   - No `parent_schedule_id` (this field is null)

2. **Schedule Instances**: For each occurrence of the recurring schedule:
   - A separate schedule record is created
   - Each instance has its own unique `schedule_id` (typically `{parent_id}-{date}`)
   - Each instance references the parent via `parent_schedule_id`
   - Instances do not have the `recurrence` field set

3. **Instance Generation**:
   - Instances are generated for the next 4-8 weeks when a recurring schedule is created
   - A background job periodically generates more instances to maintain a rolling window

4. **Handling Changes**:
   - When a parent schedule is cancelled, all future instances are also cancelled
   - Individual instances can be cancelled without affecting the parent or other instances
   - Changes to the parent can be propagated to all future instances

This approach simplifies querying for available schedules in a time range and makes matchmaking more efficient.

## Common Access Patterns

### Player Operations
- Get player by Guild ID and user_id ID: `Players[guild_id, user_id_id]`
- List all players in a guild: Query `Players` where `guild_id = {guild_id}`
- Get players by attribute in a guild: Query `Players` where `guild_id = {guild_id}` and filter by attribute

### Court Operations
- Get court by ID: `Courts[court_id]`
- Get all courts in a location: Query `Courts` using `LocationIndex` GSI where `location = {location}`

### Schedule Operations
- Get schedule by ID: `Schedules[guild_id, schedule_id]`
- Get all schedules for a user: Query `Schedules` using `UserSchedulesIndex` GSI where `user_id = {user_id}`
- Get schedules in a time range: Query `Schedules` using `StartTimeIndex` GSI
- Get upcoming schedules: Query `Schedules` using `StartTimeIndex` GSI with condition `start_time > {current_time}`
- Get instances of a recurring schedule: Query `Schedules` using `RecurringInstancesIndex` GSI where `parent_schedule_id = {parent_id}`

### Engagement Operations
- Get engagements for a user: Query `UserEngagement` using `UserIndex` GSI where `user_id = {user_id}`
- Get engagements by activity type: Query `UserEngagement` using `ActivityTypeIndex` GSI where `activity_type = {activity_type}`
- Calculate user engagement score: Sum engagement values for a user within a time period

## Multi-Server Architecture

The database is designed to support multiple user_id servers (guilds) with complete data isolation:

1. All tables use `guild_id` as part of their primary key
2. This ensures data from different servers is completely separated
3. Queries must always include the `guild_id` to retrieve the correct data
4. This approach allows for:
   - Test and production environments
   - City-specific servers in the future
   - Clean data separation between environments

## Data Types and Formats

- **Timestamps**: ISO format strings with UTC timezone (e.g., "2025-05-19T16:03:41Z")
- **Dates**: MM/DD/YYYY format (e.g., "05/19/2025")
- **IDs**: String format
- **Numeric values**: Stored as Decimal type for precision
- **Preferences**: Stored as maps for flexibility
- **Lists**: Used for multiple values (interests, roles, etc.)
- **Maps**: Used for structured data (preferences, engagement_summary, etc.)
