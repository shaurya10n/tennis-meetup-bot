from datetime import datetime
from typing import List, Optional, Dict, Any

from src.database.models.dynamodb.court import Court


class CourtDAO:
    """Data Access Object for Court model in DynamoDB."""
    
    def __init__(self, dynamodb):
        """Initialize CourtDAO with DynamoDB resource."""
        self.table = dynamodb.Table(Court.TABLE_NAME)
    
    def create_court(self, name: str, location: str, surface_type: str,
                    number_of_courts: int, is_indoor: bool, amenities: List[str],
                    google_maps_link: str, **kwargs) -> Court:
        """Create a new court in the database.
        
        Args:
            name: Court name
            location: Court location
            surface_type: Surface type (e.g., "Hard", "Clay", "Grass")
            number_of_courts: Number of courts at this location
            is_indoor: Whether the courts are indoor
            amenities: List of amenities
            google_maps_link: Google Maps link to the court
            **kwargs: Additional court attributes
            
        Returns:
            Court: The created court object
        """
        now = int(datetime.now().timestamp())
        
        court = Court(
            name=name,
            location=location,
            surface_type=surface_type,
            number_of_courts=number_of_courts,
            is_indoor=is_indoor,
            amenities=amenities,
            google_maps_link=google_maps_link,
            created_at=now,
            updated_at=now,
            **kwargs
        )
        
        self.table.put_item(Item=court.to_dict())
        return court
    
    def get_court(self, court_id: str) -> Optional[Court]:
        """Get a court by ID.
        
        Args:
            court_id: Court ID
            
        Returns:
            Optional[Court]: The court object if found, None otherwise
        """
        response = self.table.get_item(Key={'court_id': court_id})
        item = response.get('Item')
        
        if not item:
            return None
            
        return Court.from_dict(item)
    
    def update_court(self, court_id: str, **update_data) -> Court:
        """Update a court's attributes.
        
        Args:
            court_id: Court ID
            **update_data: Attributes to update
            
        Returns:
            Court: The updated court object
        """
        # Get current court data
        court = self.get_court(court_id)
        if not court:
            raise ValueError(f"Court with ID {court_id} not found")
        
        # Update attributes
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        for key, value in update_data.items():
            update_expressions.append(f"#{key} = :{key}")
            expression_values[f":{key}"] = value
            expression_names[f"#{key}"] = key
        
        # Add updated_at timestamp
        update_expressions.append("#updated_at = :updated_at")
        expression_values[":updated_at"] = int(datetime.now().timestamp())
        expression_names["#updated_at"] = "updated_at"
        
        update_expression = "SET " + ", ".join(update_expressions)
        
        # Perform update
        self.table.update_item(
            Key={'court_id': court_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values
        )
        
        # Return updated court
        return self.get_court(court_id)
    
    def delete_court(self, court_id: str) -> bool:
        """Delete a court from the database.
        
        Args:
            court_id: Court ID
            
        Returns:
            bool: True if court was deleted, False otherwise
        """
        response = self.table.delete_item(
            Key={'court_id': court_id},
            ReturnValues='ALL_OLD'
        )
        
        return 'Attributes' in response
    
    def list_courts(self) -> List[Court]:
        """List all courts in the database.
        
        Returns:
            List[Court]: List of all courts
        """
        response = self.table.scan()
        items = response.get('Items', [])
        
        courts = [Court.from_dict(item) for item in items]
        return courts
    
    def get_courts_by_location(self, location: str) -> List[Court]:
        """Get courts by location.
        
        Args:
            location: Location name
            
        Returns:
            List[Court]: List of courts at the location
        """
        # Using the LocationIndex GSI
        response = self.table.query(
            IndexName='LocationIndex',
            KeyConditionExpression="location = :location",
            ExpressionAttributeValues={
                ":location": location
            }
        )
        
        items = response.get('Items', [])
        courts = [Court.from_dict(item) for item in items]
        return courts
    
    def get_courts_by_attribute(self, attribute: str, value: Any) -> List[Court]:
        """Get courts by a specific attribute value.
        
        Args:
            attribute: Attribute name
            value: Attribute value
            
        Returns:
            List[Court]: List of matching courts
        """
        response = self.table.scan(
            FilterExpression=f"#{attribute} = :{attribute}",
            ExpressionAttributeNames={f"#{attribute}": attribute},
            ExpressionAttributeValues={f":{attribute}": value}
        )
        
        items = response.get('Items', [])
        courts = [Court.from_dict(item) for item in items]
        return courts
