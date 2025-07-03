# src/database/models/court.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Court:
    """Represents a tennis court location."""

    court_id: str
    name: str
    location: str
    surface_type: str
    number_of_courts: int
    is_indoor: bool
    amenities: List[str]
    google_maps_link: str
    description: Optional[str] = None
    cost_per_hour: Optional[float] = None
    booking_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_dict(data: Dict) -> 'Court':
        """Create a Court instance from a dictionary."""
        return Court(
            court_id=data.get('court_id'),
            name=data.get('name'),
            location=data.get('location'),
            surface_type=data.get('surface_type'),
            number_of_courts=data.get('number_of_courts'),
            is_indoor=data.get('is_indoor'),
            amenities=data.get('amenities', []),
            google_maps_link=data.get('google_maps_link'),
            description=data.get('description'),
            cost_per_hour=data.get('cost_per_hour'),
            booking_url=data.get('booking_url'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> Dict:
        """Convert Court instance to dictionary."""
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
