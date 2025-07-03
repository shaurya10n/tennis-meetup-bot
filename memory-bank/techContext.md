# Technical Context

## Technology Stack

### Core Technologies
- Python 3.13.2 (required)
- Discord.py - Discord bot framework
- DynamoDB - Database for AWS deployment
- Docker - Containerization for development and deployment
- YAML - Configuration management
- dateparser - Natural language date/time parsing
- setuptools>=69.0.0 (required for Python 3.13+ compatibility)

### Key Dependencies
```
nextcord==3.0.1
boto3==1.34.0  # AWS SDK for DynamoDB
python-dotenv==1.0.1
watchdog==6.0.0
pyyaml==6.0.2
pytest==7.4.4
pytest-asyncio==0.23.5
pytest-mock==3.12.0
pytest-cov==4.1.0
dateparser==1.2.0
rapidfuzz==3.6.1
python-dateutil==2.8.2
```

## Development Environment

### Project Structure
The project follows a modular structure:
```
meetup-bot/
├── docker/                # Docker configuration
│   ├── dev/              # Development environment
│   └── prod/             # Production environment
├── scripts/              # Utility scripts
├── src/                  # Source code
│   ├── cogs/             # Discord command modules
│   │   ├── admin/        # Admin commands
│   │   └── user/         # User commands
│   │       └── commands/
│   │           ├── schedule/      # Schedule management
│   │           │   ├── parser/    # NLP parsing
│   │           │   ├── views/     # UI components
│   │           │   └── utils/     # Helpers
│   ├── config/           # Configuration
│   ├── database/         # Data layer
│   │   ├── dao/          # Data Access Objects
│   │   │   └── dynamodb/ # DynamoDB-specific DAOs
│   │   └── models/       # Data models
│   │       └── dynamodb/ # DynamoDB-specific models
│   └── utils/            # Utilities
├── tests/                # Test suite
│   ├── parser/           # Parser-specific tests
│   │   ├── test_time_parser.py    # General parser tests
│   │   ├── next_two_weeks_test.py # Next two weeks pattern
│   │   ├── rest_of_week_test.py   # Rest of week pattern
│   │   ├── simple_parser_test.py  # Simple patterns
│   │   └── suggest_correction_test.py # Correction suggestions
│   └── integration/      # Integration tests
└── memory-bank/          # Project documentation
```

### Configuration Management
- YAML-based configuration
- Environment-specific settings
- DynamoDB configuration
- Discord bot settings
- Timezone configuration
- Docker environment variables

### Development Tools
- VSCode as primary IDE
- Git for version control
- Pytest for testing
- Docker for containerization
- DynamoDB Local for local development

## Technical Constraints

### Discord API
- Rate limiting considerations
- Command cooldowns
- Permission management
- Role hierarchy
- View timeouts (180s for lists, 60s for confirmations)

### DynamoDB
- Key-value data model
- Partition key and sort key design
- Global Secondary Indexes for efficient queries
- Item size limits (400KB)
- Query complexity considerations
- Provisioned throughput management
- Local development with DynamoDB Local

### Schedule System
- Natural language parsing with dateparser
- Timezone handling (America/Vancouver)
- Schedule conflict resolution
- View pagination limits
- Command parameter validation
- Recurrence pattern support

### Performance
- Asynchronous operation requirements
- Memory usage optimization
- Database query efficiency
- Event handling throughput

## Development Practices

### Code Style
- PEP 8 compliance
- Type hints usage
- Docstring documentation
- Clear naming conventions

### Testing Strategy
- Organized test structure
  - Parser-specific tests in dedicated directory
  - Integration tests separated
  - Clear test file naming conventions
  - Focused test cases by functionality
- Comprehensive test coverage
  - Unit tests for core logic
  - Pattern-specific test files
  - Edge case testing
  - Fuzzy matching verification
- Test organization principles
  - Group related test cases
  - Clear test descriptions
  - Consistent test structure
  - Reusable test utilities
- Quality assurance
  - Mock testing for external services
  - Test coverage monitoring
  - Continuous testing pipeline
  - Regression prevention

### Error Handling
- Comprehensive exception handling
- User-friendly error messages
- Logging for debugging
- Graceful degradation

### Security
- Environment variable usage
- Input validation
- Safe data handling
- Role-based access control

## Deployment

### Requirements
- Python 3.13.2 runtime
- setuptools>=69.0.0 (required for Python 3.13+ compatibility)
- AWS credentials for DynamoDB
- Discord bot token
- Configuration files
- Docker for containerization

### Environment Setup
1. Python virtual environment
2. Dependencies installation
3. DynamoDB configuration
4. Discord application setup
5. Docker container setup

### AWS Deployment
1. EC2 instance for hosting
2. DynamoDB tables in AWS
3. ECR for Docker image storage
4. IAM roles for permissions

### Monitoring
- Discord status monitoring
- DynamoDB usage tracking
- Error logging
- Performance metrics

## Future Considerations

### Scalability
- Database query optimization
- Caching implementation
- Background task management
- Rate limit handling

### Maintainability
- Documentation updates
- Code review process
- Version control practices
- Technical debt management

### Feature Extensions
- Multi-timezone support
- Advanced recurring schedules
- Schedule analytics
- Match history integration
- Schedule-based matchmaking

### Natural Language Processing
- Multi-layered parsing strategy
  - Primary parsing with dateparser
  - Fuzzy matching with rapidfuzz
  - Pattern-based corrections
  - Special date handling
- Time expression support
  - Complex date patterns
  - Recurring schedules
  - Time ranges with AM/PM
  - Time of day references
- Error handling and suggestions
  - Typo correction
  - Format suggestions
  - Common mistake detection
  - User guidance
- Future improvements
  - Additional time patterns
  - Enhanced fuzzy matching
  - More flexible formats
  - Learning from user input


### Architechture Diagram 
```
graph TD
    subgraph Discord Interface
        Commands --> CommandWrapper[Command Wrapper]
        Events[Event Handlers] --> EventWrapper[Event Wrapper]
    end
    subgraph Core Systems
        PM[Player Management] --> DB[(Database)]
        EM[Engagement Monitoring] --> DB
        MM[Match Making] --> DB
        SM[Schedule Management] --> DB
        RM[Role Management] --> Discord
    end

    subgraph Data Layer
        DB --> PlayerDAO[Player DAO]
        DB --> ScheduleDAO[Schedule DAO]
        DB --> CourtDAO[Court DAO]
        PlayerDAO --> PlayerModel[Player Model]
        ScheduleDAO --> ScheduleModel[Schedule Model]
        CourtDAO --> CourtModel[Court Model]
    end

    CommandWrapper --> PM
    CommandWrapper --> EM
    CommandWrapper --> MM
    CommandWrapper --> SM
    EventWrapper --> RM
    EventWrapper --> EM
```