import uuid
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal


class Court:
    """Court model for DynamoDB representing a tennis court location."""
    
    TABLE_NAME = "Courts"
    
    @staticmethod
    def create_table(dynamodb):
        """Create the Courts table in DynamoDB if it doesn't exist."""
        table = dynamodb.create_table(
            TableName=Court.TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'court_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'court_id', 'AttributeType': 'S'},
                {'AttributeName': 'location', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'LocationIndex',
                    'KeySchema': [
                        {'AttributeName': 'location', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        return table
    
    def __init__(self,
                 name: str,
                 location: str,
                 surface_type: str,
                 number_of_courts: int,
                 is_indoor: bool,
                 amenities: List[str],
                 google_maps_link: str,
                 court_id: str = None,
                 description: Optional[str] = None,
                 cost_per_hour: Optional[Decimal] = None,
                 booking_url: Optional[str] = None,
                 created_at: Optional[int] = None,  # Unix timestamp
                 updated_at: Optional[int] = None): # Unix timestamp
        """Initialize a Court instance."""
        self.court_id = court_id or str(uuid.uuid4())
        self.name = name
        self.location = location
        self.surface_type = surface_type
        self.number_of_courts = number_of_courts
        self.is_indoor = is_indoor
        self.amenities = amenities or []
        self.google_maps_link = google_maps_link
        self.description = description
        self.cost_per_hour = cost_per_hour
        self.booking_url = booking_url
        self.created_at = created_at or int(datetime.now().timestamp())
        self.updated_at = updated_at or int(datetime.now().timestamp())
    
    def to_dict(self) -> Dict:
        """Convert Court instance to dictionary for DynamoDB storage."""
        return {
            'court_id': self.court_id,
            'name': self.name,
            'location': self.location,
            'surface_type': self.surface_type,
            'number_of_courts': self.number_of_courts,
            'is_indoor': self.is_indoor,
            'amenities': self.amenities,
            'google_maps_link': self.google_maps_link,
            'description': self.description,
            'cost_per_hour': self.cost_per_hour,
            'booking_url': self.booking_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Court':
        """Create a Court instance from a dictionary."""
        # Convert timestamp fields to int if they exist
        created_at = data.get('created_at')
        if created_at is not None:
            created_at = int(created_at)
            
        updated_at = data.get('updated_at')
        if updated_at is not None:
            updated_at = int(updated_at)
            
        # Convert number_of_courts to int if it's a Decimal
        number_of_courts = data.get('number_of_courts')
        if number_of_courts is not None:
            number_of_courts = int(number_of_courts)
        
        return Court(
            court_id=data.get('court_id'),
            name=data.get('name'),
            location=data.get('location'),
            surface_type=data.get('surface_type'),
            number_of_courts=number_of_courts,
            is_indoor=data.get('is_indoor'),
            amenities=data.get('amenities', []),
            google_maps_link=data.get('google_maps_link'),
            description=data.get('description'),
            cost_per_hour=data.get('cost_per_hour'),
            booking_url=data.get('booking_url'),
            created_at=created_at,
            updated_at=updated_at
        )
