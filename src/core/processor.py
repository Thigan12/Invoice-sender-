from rapidfuzz import process, fuzz
from typing import List, Optional, Tuple
from src.database.repository import DataRepository

class ProductProcessor:
    def __init__(self):
        # Load standard names from the database for matching
        self.standard_names = DataRepository.get_master_products()

    def find_match(self, input_name: str, threshold: int = 80) -> Tuple[str, bool]:
        """
        Tries to find a fuzzy match for a product name.
        Returns (matched_name, is_exact_or_fuzzy)
        """
        if not input_name:
            return "", False
            
        input_name = input_name.strip()
        
        # 1. Check for exact match first
        if input_name in self.standard_names:
            return input_name, True
            
        # 2. Try fuzzy matching
        if self.standard_names:
            match = process.extractOne(input_name, self.standard_names, scorer=fuzz.WRatio)
            if match and match[1] >= threshold:
                return match[0], True
        
        # 3. No good match found
        return input_name, False

    def add_standard_name(self, name: str, price: float = 0.0):
        """Adds a new name to the master list and database (learning mode)."""
        if name and name not in self.standard_names:
            DataRepository.add_master_product(name, price)
            self.standard_names.append(name)
