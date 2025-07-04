from src.config.dynamodb_config import get_db
from src.database.models.dynamodb import Player, Schedule, Court, UserEngagement, Match


def init_database():
    """Initialize DynamoDB tables if they don't exist."""
    dynamodb = get_db()
    
    # Create tables if they don't exist
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']
    
    if Player.TABLE_NAME not in existing_tables:
        print(f"Creating {Player.TABLE_NAME} table...")
        Player.create_table(dynamodb)
    
    if Schedule.TABLE_NAME not in existing_tables:
        print(f"Creating {Schedule.TABLE_NAME} table...")
        Schedule.create_table(dynamodb)
    
    if Court.TABLE_NAME not in existing_tables:
        print(f"Creating {Court.TABLE_NAME} table...")
        Court.create_table(dynamodb)
    
    if UserEngagement.TABLE_NAME not in existing_tables:
        print(f"Creating {UserEngagement.TABLE_NAME} table...")
        UserEngagement.create_table(dynamodb)
    
    if Match.TABLE_NAME not in existing_tables:
        print(f"Creating {Match.TABLE_NAME} table...")
        Match.create_table(dynamodb)
    
    print("Database initialization complete!")


if __name__ == "__main__":
    init_database()
