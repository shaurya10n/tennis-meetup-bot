"""Enhanced natural language parser for schedule time descriptions."""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
import dateparser
import logging
from zoneinfo import ZoneInfo
import re
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from rapidfuzz import fuzz, process
from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class TimeParser:
    """Enhanced parser for natural language time descriptions."""

    def __init__(self):
        """Initialize parser with timezone settings."""
        config_loader = ConfigLoader()
        self.timezone = config_loader.get_timezone()
        self.settings = {
            'TIMEZONE': str(self.timezone),
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now(self.timezone),
            'STRICT_PARSING': False,  # More forgiving parsing
            'PREFER_DAY_OF_MONTH': 'current',
        }
        
        # Common time expressions for fuzzy matching
        self.common_expressions = [
            "today", "tomorrow", "next week", "this week", "next month",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "every monday", "every tuesday", "every wednesday", "every thursday", 
            "every friday", "every saturday", "every sunday",
            "next monday", "next tuesday", "next wednesday", "next thursday",
            "next friday", "next saturday", "next sunday",
            "morning", "afternoon", "evening", "night",
            "next two weeks", "rest of the week", "weekend"
        ]
        
        # Regex patterns for time formats
        self.time_patterns = {
            # Time range patterns
            'time_range': r'(\d{1,2})(?::(\d{1,2}))?\s*([ap]m)?\s*(?:to|-)\s*(\d{1,2})(?::(\d{1,2}))?\s*([ap]m)?',
            
            # Recurrence patterns
            'every_day': r'every\s+day(?:s)?',
            'every_weekday': r'every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            'every_week': r'every\s+week',
            'every_month': r'every\s+month',
            
            # Date range patterns
            'next_n_weeks': r'next\s+(?:(\d+)|two|three|four)\s+weeks?',
            'next_n_days': r'next\s+(\d+)\s+days?',
            'rest_of_week': r'rest\s+of\s+(?:the\s+)?week',
            'this_week': r'this\s+week',
            'next_week': r'next\s+week',
            'weekend': r'(?:this\s+)?weekend',
            
            # Complex date patterns
            'next_week_day': r'next\s+week\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            'day_of_week': r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            
            # Time of day patterns
            'morning': r'morning',
            'afternoon': r'afternoon',
            'evening': r'evening',
            'night': r'night',
        }

    def parse_time_description(self, description: str) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """Parse a natural language time description with multi-layered approach.
        
        Args:
            description (str): Time description (e.g., "today 4-6pm", "next week tuesday 3pm")

        Returns:
            Tuple[Optional[datetime], Optional[datetime], str]:
                - Start time or None if invalid
                - End time or None if invalid
                - Error message if any, empty string if successful
        """
        try:
            logger.info(f"Parsing time description: '{description}'")
            original_description = description
            
            # Step 1: Try fuzzy matching to correct potential typos
            description = self._apply_fuzzy_correction(description)
            if description != original_description:
                logger.info(f"Fuzzy corrected: '{original_description}' -> '{description}'")
            
            # Step 2: Check for recurrence patterns
            recurrence_info = self._extract_recurrence_pattern(description)
            if recurrence_info:
                recurrence_type, recurrence_value = recurrence_info
                
                # Store recurrence info for later use
                logger.info(f"Detected recurrence: {recurrence_type} {recurrence_value}")
                
                # For weekly recurrence on specific day, add the day name to the description
                if recurrence_type == 'weekly' and recurrence_value not in ['week']:
                    # Add the day name to the description for better parsing
                    day_name = recurrence_value
                    description = re.sub(
                        r'every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                        f"next {day_name}", description, flags=re.IGNORECASE
                    )
                else:
                    # Remove recurrence pattern for date parsing
                    description = re.sub(
                        r'every\s+(day|week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                        '', description, flags=re.IGNORECASE
                    ).strip()
                    
                    # If the description is now empty, add a default date (tomorrow)
                    if not description:
                        description = "tomorrow"
            
            # Step 3: Extract time range if present
            time_range_match = re.search(self.time_patterns['time_range'], description, re.IGNORECASE)
            if time_range_match:
                # Process time range
                start_time, end_time, error = self._process_time_range(description, time_range_match)
                if error:
                    # Try to suggest a correction instead of alternative parsing
                    suggestion = self.suggest_correction(original_description)
                    if suggestion and suggestion != original_description:
                        logger.info(f"Suggesting correction: '{original_description}' -> '{suggestion}'")
                        return None, None, f"{error} Did you mean '{suggestion}'?"
                    return None, None, error
                
            else:
                # Try parsing as a single datetime or using special patterns
                start_time, end_time, error = self._process_special_patterns(description)
                if error:
                    # Try to suggest a correction instead of alternative parsing
                    suggestion = self.suggest_correction(original_description)
                    if suggestion and suggestion != original_description:
                        logger.info(f"Suggesting correction: '{original_description}' -> '{suggestion}'")
                        return None, None, f"{error} Did you mean '{suggestion}'?"
                    return None, None, error
            
            # Validate times
            if start_time >= end_time:
                logger.warning(f"Invalid time range: end ({end_time}) not after start ({start_time})")
                return None, None, "End time must be after start time"
            
            # Debug logging for time comparison
            now_in_tz = datetime.now(self.timezone)
            logger.info(f"DEBUG: Comparing start_time={start_time} to now_in_tz={now_in_tz} (timezone={self.timezone})")
            
            if start_time < now_in_tz:
                logger.warning(f"Time in past: {start_time}")
                return None, None, "Cannot create schedule in the past"

            # Check duration
            duration = (end_time - start_time).total_seconds() / 3600  # hours
            if duration > 4:
                logger.warning(f"Duration too long: {duration} hours")
                return None, None, "Schedule duration cannot exceed 4 hours"
            if duration < 0.5:
                logger.warning(f"Duration too short: {duration} hours")
                return None, None, "Schedule duration must be at least 30 minutes"

            logger.info(f"Successfully parsed times - Start: {start_time}, End: {end_time}")
            return start_time, end_time, ""

        except Exception as e:
            logger.error(f"Error parsing time description: {e}", exc_info=True)
            return None, None, f"Error parsing time description: {str(e)}"

    def _apply_fuzzy_correction(self, text: str) -> str:
        """Apply fuzzy matching to correct common typos in time expressions.
        
        Args:
            text (str): Input text with potential typos
            
        Returns:
            str: Corrected text
        """
        # Split the input into words
        words = text.lower().split()
        corrected_words = []
        
        for word in words:
            # Skip short words and numbers
            if len(word) <= 2 or word.isdigit() or '-' in word:
                corrected_words.append(word)
                continue
                
            # Check if this word needs correction
            matches = process.extract(word, self.common_expressions, scorer=fuzz.ratio, limit=1)
            if matches and matches[0][1] > 80:  # 80% similarity threshold
                best_match = matches[0][0]
                # Only replace if it's a single word in our common expressions
                if ' ' not in best_match:
                    corrected_words.append(best_match)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
                
        return ' '.join(corrected_words)

    def _extract_recurrence_pattern(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract recurrence pattern from text.
        
        Args:
            text (str): Input text
            
        Returns:
            Optional[Tuple[str, str]]: (recurrence_type, value) or None if no pattern found
        """
        # Check for daily recurrence
        if re.search(self.time_patterns['every_day'], text, re.IGNORECASE):
            return ('daily', 'day')
            
        # Check for weekly recurrence on specific day
        weekday_match = re.search(self.time_patterns['every_weekday'], text, re.IGNORECASE)
        if weekday_match:
            return ('weekly', weekday_match.group(1).lower())
            
        # Check for weekly recurrence
        if re.search(self.time_patterns['every_week'], text, re.IGNORECASE):
            return ('weekly', 'week')
            
        # Check for monthly recurrence
        if re.search(self.time_patterns['every_month'], text, re.IGNORECASE):
            return ('monthly', 'month')
            
        return None

    def _process_time_range(self, description: str, time_range_match) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """Process a time range match.
        
        Args:
            description (str): Full time description
            time_range_match: Regex match object for time range
            
        Returns:
            Tuple[Optional[datetime], Optional[datetime], str]:
                - Start time or None if invalid
                - End time or None if invalid
                - Error message if any, empty string if successful
        """
        # Remove the time range for initial date parsing
        date_part = re.sub(self.time_patterns['time_range'], '', description, flags=re.IGNORECASE).strip()
        
        # Handle special date patterns
        base_date = self._parse_special_date_patterns(date_part)
        
        # If no special pattern matched, use dateparser
        if not base_date:
            base_date = dateparser.parse(date_part, settings=self.settings)
            
        if not base_date:
            # Try to provide a helpful suggestion for day abbreviations
            day_abbrevs = {
                'mon': 'monday', 'tue': 'tuesday', 'tues': 'tuesday',
                'wed': 'wednesday', 'weds': 'wednesday', 
                'thu': 'thursday', 'thur': 'thursday', 'thurs': 'thursday',
                'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
            }
            
            words = date_part.lower().split()
            if words and words[0] in day_abbrevs:
                suggestion = f"Did you mean '{day_abbrevs[words[0]]}'? Try using '{day_abbrevs[words[0]]}' instead."
                logger.warning(f"Could not parse date part: '{date_part}'. Suggesting: {suggestion}")
                return None, None, f"Could not understand date: '{date_part}'. {suggestion}"
            else:
                logger.warning(f"Could not parse date part: '{date_part}'")
                return None, None, f"Could not understand date: '{date_part}'. Please use a format like 'monday 4-5pm' or 'tomorrow 3-4pm'."

        # Extract time components
        start_hour = int(time_range_match.group(1))
        start_min = int(time_range_match.group(2) or 0)
        start_meridiem = time_range_match.group(3)
        end_hour = int(time_range_match.group(4))
        end_min = int(time_range_match.group(5) or 0)
        end_meridiem = time_range_match.group(6)

        # Handle meridiem (AM/PM)
        if start_meridiem:
            start_meridiem = start_meridiem.lower()
        if end_meridiem:
            end_meridiem = end_meridiem.lower()
            
        # If only one meridiem is specified, use it for both times
        if start_meridiem and not end_meridiem:
            end_meridiem = start_meridiem
        elif end_meridiem and not start_meridiem:
            start_meridiem = end_meridiem
        
        # If no meridiem is specified, default to PM for times between 1-11
        if not start_meridiem:
            start_meridiem = 'pm' if 1 <= start_hour <= 11 else 'am'
        if not end_meridiem:
            end_meridiem = 'pm' if 1 <= end_hour <= 11 else 'am'
            
        # If end time is less than start time and they have the same meridiem, assume spanning AM/PM
        if end_hour < start_hour and start_meridiem == end_meridiem:
            end_meridiem = 'pm' if start_meridiem == 'am' else 'am'

        # Create start and end times with clean seconds/microseconds
        start_time = base_date.replace(
            hour=start_hour + (12 if start_meridiem == 'pm' and start_hour != 12 else 0),
            minute=start_min,
            second=0,
            microsecond=0
        )
        end_time = base_date.replace(
            hour=end_hour + (12 if end_meridiem == 'pm' and end_hour != 12 else 0),
            minute=end_min,
            second=0,
            microsecond=0
        )
        
        return start_time, end_time, ""

    def _parse_special_date_patterns(self, date_part: str) -> Optional[datetime]:
        """Parse special date patterns that dateparser might struggle with.
        
        Args:
            date_part (str): Date part of the description
            
        Returns:
            Optional[datetime]: Parsed date or None if no pattern matched
        """
        date_part = date_part.lower().strip()
        now = datetime.now(self.timezone)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Handle "next X weeks"
        next_weeks_match = re.search(self.time_patterns['next_n_weeks'], date_part)
        if next_weeks_match:
            if next_weeks_match.group(1):
                weeks = int(next_weeks_match.group(1))
            else:
                # Handle text numbers
                if 'two' in date_part:
                    weeks = 2
                elif 'three' in date_part:
                    weeks = 3
                elif 'four' in date_part:
                    weeks = 4
                else:
                    weeks = 1
            return today + timedelta(days=weeks*7)
            
        # Handle "next X days"
        next_days_match = re.search(self.time_patterns['next_n_days'], date_part)
        if next_days_match:
            days = int(next_days_match.group(1))
            return today + timedelta(days=days)
            
        # Handle "rest of the week"
        if re.search(self.time_patterns['rest_of_week'], date_part):
            return today
            
        # Handle "this week"
        if re.search(self.time_patterns['this_week'], date_part):
            return today
            
        # Handle "next week day" (e.g., "next week tuesday")
        next_week_day_match = re.search(self.time_patterns['next_week_day'], date_part)
        if next_week_day_match:
            day_name = next_week_day_match.group(1).lower()
            day_num = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, 
                      "friday": 4, "saturday": 5, "sunday": 6}[day_name]
            
            # Calculate days until target day in next week
            current_weekday = today.weekday()  # 0-6 (Monday-Sunday)
            
            # First calculate days to get to next week's start (Monday)
            days_to_next_monday = (7 - current_weekday)  # This gets us to next Monday
            
            # Then add the target day offset (0 for Monday, 1 for Tuesday, etc.)
            total_days = days_to_next_monday + day_num
            
            # Return the date
            return today + timedelta(days=total_days)

        # Handle "next week" (must come after "next week day" to avoid premature matching)
        if re.search(self.time_patterns['next_week'], date_part):
            return today + timedelta(days=7)
            
        # Handle "weekend"
        if re.search(self.time_patterns['weekend'], date_part):
            # Find the next Saturday
            days_until_saturday = (5 - now.weekday()) % 7
            if days_until_saturday == 0:  # Today is Saturday
                return today
            return today + timedelta(days=days_until_saturday)
            
        # Handle "next day" (e.g., "next monday")
        next_day_match = re.search(r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_part, re.IGNORECASE)
        if next_day_match:
            day_name = next_day_match.group(1).lower()
            day_num = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, 
                      "friday": 4, "saturday": 5, "sunday": 6}[day_name]
            
            # Calculate days until the next occurrence of this day
            days_until = (day_num - today.weekday()) % 7
            if days_until == 0:  # If today is the same day, go to next week
                days_until = 7
                
            return today + timedelta(days=days_until)
            
        return None

    def _process_special_patterns(self, description: str) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """Process special time patterns like morning, afternoon, etc.
        
        Args:
            description (str): Time description
            
        Returns:
            Tuple[Optional[datetime], Optional[datetime], str]:
                - Start time or None if invalid
                - End time or None if invalid
                - Error message if any, empty string if successful
        """
        # Try parsing as a single datetime
        parsed_time = dateparser.parse(description, settings=self.settings)
        
        if not parsed_time:
            # Check for time of day patterns
            base_date = None
            start_hour = 0
            end_hour = 0
            
            # Extract date part (remove time of day references)
            date_part = description
            for pattern in ['morning', 'afternoon', 'evening', 'night']:
                date_part = re.sub(self.time_patterns[pattern], '', date_part, flags=re.IGNORECASE).strip()
            
            # Parse the date part
            if date_part:
                base_date = self._parse_special_date_patterns(date_part)
                if not base_date:
                    base_date = dateparser.parse(date_part, settings=self.settings)
            
            if not base_date:
                # Try to provide a helpful suggestion for day abbreviations
                day_abbrevs = {
                    'mon': 'monday', 'tue': 'tuesday', 'tues': 'tuesday',
                    'wed': 'wednesday', 'weds': 'wednesday', 
                    'thu': 'thursday', 'thur': 'thursday', 'thurs': 'thursday',
                    'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
                }
                
                words = date_part.lower().split()
                if words and words[0] in day_abbrevs:
                    suggestion = f"Did you mean '{day_abbrevs[words[0]]}'? Try using '{day_abbrevs[words[0]]}' instead."
                    logger.warning(f"Could not parse date part in special pattern: '{date_part}'. Suggesting: {suggestion}")
                    return None, None, f"Could not understand time format: '{description}'. {suggestion}"
                else:
                    logger.warning(f"Could not parse date part in special pattern: '{date_part}'")
                    return None, None, f"Could not understand time format: '{description}'. Please use a format like 'monday 4-5pm' or 'tomorrow afternoon'."
                
            # Determine time range based on time of day
            if re.search(self.time_patterns['morning'], description, re.IGNORECASE):
                start_hour = 8
                end_hour = 11
            elif re.search(self.time_patterns['afternoon'], description, re.IGNORECASE):
                start_hour = 12
                end_hour = 16
            elif re.search(self.time_patterns['evening'], description, re.IGNORECASE):
                start_hour = 17
                end_hour = 20
            elif re.search(self.time_patterns['night'], description, re.IGNORECASE):
                start_hour = 19
                end_hour = 22
            else:
                # Default to a reasonable time range
                start_hour = 9
                end_hour = 11
                
            # Create start and end times
            start_time = base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = base_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            
        else:
            # Default to 2-hour duration with clean seconds/microseconds
            start_time = parsed_time.replace(second=0, microsecond=0)
            end_time = (start_time + timedelta(hours=2)).replace(second=0, microsecond=0)
            
        return start_time, end_time, ""

    def _try_alternative_parsing(self, description: str) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """Try alternative parsing methods when standard parsing fails.
        
        Args:
            description (str): Original time description
            
        Returns:
            Tuple[Optional[datetime], Optional[datetime], str]:
                - Start time or None if invalid
                - End time or None if invalid
                - Error message if any, empty string if successful
        """
        # Try with different dateparser settings
        alternative_settings = self.settings.copy()
        alternative_settings['PREFER_DATES_FROM'] = 'current_period'
        
        try:
            # Try parsing with alternative settings
            parsed_time = dateparser.parse(description, settings=alternative_settings)
            if parsed_time:
                start_time = parsed_time.replace(second=0, microsecond=0)
                end_time = (start_time + timedelta(hours=2)).replace(second=0, microsecond=0)
                return start_time, end_time, ""
                
            # Try extracting just numbers for time
            time_only_match = re.search(r'(\d{1,2})(?::(\d{1,2}))?\s*([ap]m)?', description, re.IGNORECASE)
            if time_only_match:
                hour = int(time_only_match.group(1))
                minute = int(time_only_match.group(2) or 0)
                meridiem = time_only_match.group(3) or 'pm'
                
                if meridiem.lower() == 'pm' and hour < 12:
                    hour += 12
                    
                today = datetime.now(self.timezone).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                
                if today < datetime.now(self.timezone):
                    today = today + timedelta(days=1)
                    
                return today, today + timedelta(hours=2), ""
                
            # Suggest a correction
            suggestion = self.suggest_correction(description)
            if suggestion:
                logger.info(f"Suggesting correction: '{description}' -> '{suggestion}'")
                return self.parse_time_description(suggestion)
                
            return None, None, "Could not understand time format"
            
        except Exception as e:
            logger.error(f"Error in alternative parsing: {e}", exc_info=True)
            return None, None, f"Error parsing time: {str(e)}"

    def suggest_correction(self, text: str) -> Optional[str]:
        """Suggest a correction for invalid input.
        
        Args:
            text (str): Invalid input text

        Returns:
            Optional[str]: Suggested correction or None if no suggestion
        """
        try:
            # Apply fuzzy matching first
            corrected_text = self._apply_fuzzy_correction(text)
            if corrected_text != text:
                return corrected_text
                
            # Common patterns to check
            patterns = [
                # Time format corrections
                (r'(\d{1,2})\s*-\s*(\d{1,2})$', r'\1-\2pm'),  # Add pm to bare times
                (r'(\d{1,2})(\d{2})-(\d{1,2})(\d{2})', r'\1:\2-\3:\4'),  # Fix military time format
                (r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', r'\1:\2-\3:\4pm'),  # Add pm to time range with colons
                (r'(\d{1,2})([ap]m)-(\d{1,2})$', r'\1-\3\2'),  # Add missing meridiem to end time
                
                # Spacing corrections
                (r'next(\w+day)', r'next \1'),  # Fix spacing in next weekday
                (r'every(\w+day)', r'every \1'),  # Fix spacing in every weekday
                (r'next(\w+)', r'next \1'),  # Fix spacing in next X
                (r'this(\w+)', r'this \1'),  # Fix spacing in this X
                
                # Abbreviation expansions
                (r'\btmrw\b', r'tomorrow'),  # Expand common abbreviations
                (r'\btmr\b', r'tomorrow'),
                (r'\baft\b', r'afternoon'),
                (r'\baftrn\b', r'afternoon'),
                (r'\beve\b', r'evening'),
                (r'\bmorn\b', r'morning'),
                
                # Day name corrections
                (r'\bmon\b', r'monday'),
                (r'\btue\b', r'tuesday'),
                (r'\btues\b', r'tuesday'),
                (r'\bwed\b', r'wednesday'),
                (r'\bweds\b', r'wednesday'),
                (r'\bthu\b', r'thursday'),
                (r'\bthur\b', r'thursday'),
                (r'\bthurs\b', r'thursday'),
                (r'\bfri\b', r'friday'),
                (r'\bsat\b', r'saturday'),
                (r'\bsun\b', r'sunday'),
                
                # Complex corrections
                (r'nxt\s+wk', r'next week'),
                (r'nxt\s+week', r'next week'),
                (r'nxt', r'next'),
                (r'wk', r'week'),
                
                # Common typos
                (r'nexxt', r'next'),
                (r'evry', r'every'),
                
                # Time of day without context
                (r'^(morning|afternoon|evening|night)$', r'today \1'),
            ]

            # Apply patterns in sequence to allow for multiple corrections
            current_text = text
            for pattern, replacement in patterns:
                if re.search(pattern, current_text, re.IGNORECASE):
                    current_text = re.sub(pattern, replacement, current_text, flags=re.IGNORECASE)
            
            # If changes were made, return the corrected text
            if current_text != text:
                return current_text

            # Try adding common words
            prefixes = ["today ", "tomorrow ", "next week "]
            for prefix in prefixes:
                suggestion = prefix + text
                if dateparser.parse(suggestion, settings=self.settings):
                    return suggestion
                    
            # Try adding meridiem to times
            if re.search(r'\d{1,2}-\d{1,2}', text):
                suggestion = re.sub(r'(\d{1,2})-(\d{1,2})', r'\1-\2pm', text)
                return suggestion
                
            # Try adding meridiem to end times
            if re.search(r'\d{1,2}[ap]m-\d{1,2}', text):
                meridiem = 'am' if 'am' in text.lower() else 'pm'
                suggestion = re.sub(r'(\d{1,2}[ap]m)-(\d{1,2})', fr'\1-\2{meridiem}', text)
                return suggestion

            return None

        except Exception as e:
            logger.error(f"Error suggesting correction: {e}", exc_info=True)
            return None
