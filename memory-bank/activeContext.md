# Active Context

## Current Focus
1. Database migration from Firebase to DynamoDB for AWS deployment
2. Player profile and NTRP rating system
3. Community engagement tracking
4. Intelligent matchmaking system
5. Schedule management system with natural language understanding

## Recent Changes
- Migrated database from Firebase to DynamoDB
- Created DynamoDB models for Player, Schedule, and Court
- Implemented Data Access Objects (DAOs) for DynamoDB
- Set up Docker containerization for development and production
- Created database initialization and seed data scripts
- Added documentation for DynamoDB setup and usage
- Fixed "next week day" pattern parsing to correctly handle all weekdays
- Improved pattern matching order to prioritize specific patterns over general ones
- Implemented enhanced natural language parsing with dateparser and rapidfuzz
- Added multi-layered parsing strategy with fuzzy matching
- Enhanced time parsing with better AM/PM handling
- Added support for recurring schedules
- Improved test organization with dedicated parser tests directory
- Added comprehensive test coverage for time parsing
- Implemented location-based availability dashboard as admin command
- Created dashboard views for availability by location and currently playing users
- Added schedule data aggregation by location and time slot
- Updated dashboard to use court locations from the database
- Improved location fallback logic for schedules without specified locations
- Implemented skill level roles based on NTRP ratings with emoji prefixes
- Added automatic role assignment during profile creation and updates
- Created shared permission system for skill level roles
- Integrated role assignment into get-started and update-profile flows

## Active Decisions

### Database Migration
- ✅ DynamoDB Models
  - Player model with partition key on discord_id
  - Schedule model with composite key (player_id, schedule_id)
  - Court model with partition key on court_id
  - Global Secondary Indexes for efficient queries
- ✅ Data Access Layer
  - DAO pattern for database operations
  - Consistent error handling
  - Transaction support
  - Batch operations
- ✅ Deployment Strategy
  - Docker containerization
  - Local development with DynamoDB Local
  - Production deployment to AWS
  - Environment-specific configurations

### Schedule Management System
- ✅ Enhanced natural language parsing
  - Multi-layered parsing strategy
  - Pattern matching priority system
  - Fuzzy matching for typo correction
  - Support for complex time expressions
  - Recurring schedule patterns
  - Timezone awareness
  - Flexible input formats
  - Suggestion system for invalid inputs
- ✅ Schedule data model
  - Recurrence patterns
  - Validation rules
  - Conflict detection
- ✅ User interface
  - Intuitive command formats
  - Clear error messages
  - Example-based help

### Community Engagement System
- ✅ Availability Dashboard
  - Location-based organization
  - Weekly time slot view (Morning/Afternoon/Evening)
  - Currently playing view
  - Admin commands for viewing and posting
  - Interactive navigation between locations
  - Posted to #hotspots channel for community visibility
- Planning engagement-based perks system
- Defining activity metrics
- Structuring role management

### Matchmaking Algorithm
- Planning feedback collection system
- Designing match recommendation logic
- Integrating schedule compatibility
- Structuring continuous learning approach

### Player Management
- NTRP rating assessment flow
- Profile data structure
- Activity tracking metrics
- Location-based matching parameters

### Role Management
- ✅ Skill Level Roles
  - Emoji-prefixed roles (🌱 Beginner, 🎾 Advanced Beginner, etc.)
  - Automatic assignment based on NTRP rating
  - Higher position in role hierarchy than Club Member
  - Consistent permissions across skill levels
- Planning activity-based roles
- Planning achievement-based roles
- Planning engagement metrics

## Current Patterns & Preferences

### Code Organization
- Modular cog-based structure
- Clear separation of concerns
- DAO pattern for data access
- Event-driven architecture
- Docker containerization

### Development Focus
- Clean, maintainable code
- Comprehensive documentation
- Robust error handling
- User-friendly interactions
- AWS-ready deployment

## Project Insights

### Key Learnings
- DynamoDB key design is critical for performance
- Docker simplifies development and deployment
- Pattern matching order is crucial for accurate parsing
- Natural language understanding improves UX
- Timezone handling is critical
- Recurrence patterns add flexibility
- Clear examples help users
- Specific patterns should take precedence over general ones

### Critical Considerations
1. Database Design
   - Key structure for efficient queries
   - Global Secondary Indexes for flexible access patterns
   - Consistent item structure
   - Batch operations for performance

2. Schedule Management
   - Natural language parsing accuracy
   - Timezone handling
   - Recurrence pattern support
   - Conflict resolution

3. Engagement Metrics
   - Match participation
   - Channel activity
   - Community contribution
   - Response rates

4. Role Management
   - Activity thresholds
   - Permission levels
   - Automated transitions
   - Inactive handling

5. Matchmaking
   - Schedule compatibility
   - Feedback integration
   - Skill matching
   - Location factors

## Next Steps

1. Complete AWS Deployment Setup
   - Finalize EC2 instance configuration
   - Set up DynamoDB tables in AWS
   - Configure IAM roles and permissions
   - Implement monitoring and logging

2. Complete Schedule System
   - Test natural language parsing
   - Implement recurrence handling
   - Add timezone configuration
   - Create schedule analytics

3. Community System
   - Implement activity tracking
   - Create leaderboard system
   - Develop perks mechanism

4. Role Management
   - Create activity monitoring
   - Implement role automation
   - Set up inactive handling

### Upcoming Considerations
- Multi-timezone support
- Advanced recurring schedules
- Schedule analytics
- Match history tracking
- Activity score calculation
- Backup and recovery procedures
- Monitoring and alerting
