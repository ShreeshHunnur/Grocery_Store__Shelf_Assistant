#!/usr/bin/env python3
"""
Deterministic data generator for the Retail Shelf Assistant database.
Generates 1000-3000 realistic products across diverse categories.
"""
import sqlite3
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ProductDataGenerator:
    """Deterministic generator for realistic product data."""
    
    def __init__(self, seed: int = 42):
        """Initialize with fixed seed for reproducible results."""
        random.seed(seed)
        self.seed = seed
        
        # Categories tailored for an Indian retail grocery store
        self.categories = [
            {"name": "Fresh Fruits", "description": "Fresh seasonal fruits", "parent": None},
            {"name": "Fresh Vegetables", "description": "Fresh regional vegetables", "parent": None},
            {"name": "Pulses & Lentils", "description": "Toor, Moong, Chana, Masoor and other dals", "parent": None},
            {"name": "Rice & Grains", "description": "Basmati, Sona Masuri, rice mixes and other grains", "parent": None},
            {"name": "Atta & Flours", "description": "Wheat flour, maida, besan, rava", "parent": None},
            {"name": "Spices & Masalas", "description": "Whole and ground spices, masala mixes", "parent": None},
            {"name": "Oils & Ghee", "description": "Cooking oils, ghee and specialty oils", "parent": None},
            {"name": "Dairy & Eggs", "description": "Milk, ghee, paneer, butter, yogurt and eggs", "parent": None},
            {"name": "Tea & Coffee", "description": "Indian tea brands, coffee and instant mixes", "parent": None},
            {"name": "Snacks & Namkeen", "description": "Chips, namkeen, biscuits, savory snacks", "parent": None},
            {"name": "Instant & Ready-to-Eat", "description": "Noodles, mixes, ready-to-eat meals", "parent": None},
            {"name": "Pickles & Chutneys", "description": "Regional pickles and chutneys", "parent": None},
            {"name": "Sweets & Mithai", "description": "Packaged Indian sweets and desserts", "parent": None},
            {"name": "Beverages", "description": "Juices, soft drinks, traditional drinks", "parent": None},
            {"name": "Bakery", "description": "Bread, rusks, cakes, biscuits", "parent": None},
            {"name": "Frozen Foods", "description": "Frozen vegetables, snacks and parathas", "parent": None},
            {"name": "Personal Care", "description": "Soap, hair care, oral care", "parent": None},
            {"name": "Household & Cleaning", "description": "Detergents, cleaners, paper products", "parent": None},
            {"name": "Baby & Kids", "description": "Baby food, diapers, baby care", "parent": None},
            {"name": "Health & Wellness", "description": "Ayurvedic and health supplements", "parent": None},
            {"name": "Pet Care", "description": "Pet food and accessories", "parent": None},
        ]
        
        # Brands commonly found in Indian retail
        self.brands = [
            # Major Indian FMCG
            "Amul", "Mother Dairy", "Britannia", "Parle", "Haldiram's", "MDH", "Everest", "Tata",
            "Maggi", "Nestle India", "ITC", "Dabur", "Himalaya", "Patanjali", "Godrej",
            "Gits", "MTR", "Aashirvaad", "Fortune", "Dhara", "Saffola", "Ashirwad",

            # Beverages and snacks
            "Frooti", "Maaza", "Limca", "Thums Up", "Minute Maid", "Parle Agro", "PepsiCo India", "Coca-Cola India",
            "Lay's (India)", "Balaji", "Bikano", "Bingo!", "Kurkure", "Haldiram", "ITC Sunfeast",

            # Dairy and staples
            "Amul Gold", "Gowardhan", "Aavin", "Nandini", "KRBL (Daawat)", "India Gate", "Tilda",

            # Spices and masalas
            "MDH", "Everest", "Tata Sampann", "Catch", "Badshah",

            # Personal care / household
            "Hindustan Unilever", "Godrej Consumer", "Colgate-Palmolive India", "P&G India", "Surf Excel", "Harpic",

            # Regional / specialty
            "Keventers", "Amul Mithai", "Lijjat", "MTR Foods", "MTR Ready", "Gits",

            # Others
            "Patanjali Ayurved", "Dabur Amla", "Bournvita India", "Bru Coffee", "Tata Tea", "Brooke Bond",
        ]

        # Add a few local/regional and category-specific brands that were missing
        # so we can map brands to categories and avoid nonsensical pairings.
        self.brands.extend([
            "Local Vendor", "Organic Farms", "Mother's Recipe", "Priya", "McCain",
            "Pampers India", "Huggies", "Pedigree", "Whiskas", "Drools"
        ])
        
        # Product name templates by category (India-specific)
        self.product_templates = {
            "Fresh Fruits": [
                "Fresh {fruit} - {size}",
                "{fruit} ({variety})",
                "Organic {fruit}",
                "Local {fruit} - {size}"
            ],
            "Fresh Vegetables": [
                "Fresh {vegetable}",
                "{vegetable} - {variety}",
                "Organic {vegetable}",
                "Pack of {size} {vegetable}s"
            ],
            "Pulses & Lentils": [
                "{brand} {pulse}",
                "{pulse} - {weight}kg",
                "Premium {pulse} - {brand}"
            ],
            "Rice & Grains": [
                "{brand} {rice_variety} Basmati - {weight}kg",
                "{rice_variety} Rice - {weight}kg",
                "Sona Masuri {brand} - {weight}kg"
            ],
            "Atta & Flours": [
                "{brand} Atta - {weight}kg",
                "Besan {brand} - {weight}kg",
                "Maida {brand} - {weight}kg"
            ],
            "Spices & Masalas": [
                "{brand} {spice}",
                "{brand} {masala} Masala",
                "Whole {spice} - {weight}g"
            ],
            "Oils & Ghee": [
                "{brand} {oil_type} Oil - {weight}L",
                "{brand} Ghee - {weight}kg",
                "Cold Pressed {oil_type} Oil {brand} - {weight}L"
            ],
            "Dairy & Eggs": [
                "{brand} {dairy_product} - {size}",
                "Fresh {dairy_product} ({brand})",
                "Pack of {size} {dairy_product}s"
            ],
            "Tea & Coffee": [
                "{brand} {tea_type} Tea - {weight}g",
                "Instant {brand} Coffee - {weight}g"
            ],
            "Snacks & Namkeen": [
                "{brand} {snack_type} - {weight}g",
                "{brand} {namkeen}",
                "Family Pack {brand} {snack_type}"
            ],
            "Instant & Ready-to-Eat": [
                "{brand} {instant} - {weight}g",
                "Ready-to-Eat {brand} {meal}"
            ],
            "Pickles & Chutneys": [
                "{brand} {pickle} - {weight}g",
                "Mango {brand} Pickle - {weight}g"
            ],
            "Sweets & Mithai": [
                "{brand} {sweet} Pack",
                "Assorted {brand} Mithai Box"
            ],
            "Beverages": [
                "{brand} {beverage_type} - {size}",
                "Traditional {beverage_type} ({brand})"
            ],
            "Bakery": [
                "{brand} Bread - {size}g",
                "Rusk {brand} - {weight}g"
            ],
            "Frozen Foods": [
                "{brand} Frozen {item}",
                "Frozen Paratha {brand} - {pack_size}"
            ],
            "Personal Care": [
                "{brand} {personal_item}",
                "{brand} {personal_item} - {size}ml"
            ],
            "Household & Cleaning": [
                "{brand} Detergent - {weight}g",
                "{brand} Cleaner - {size}ml"
            ],
            "Baby & Kids": [
                "{brand} Baby Food - {weight}g",
                "{brand} Diapers - Size {size}"
            ],
            "Health & Wellness": [
                "{brand} Ayurvedic {product}",
                "{brand} Supplement - {weight}g"
            ],
            "Pet Care": [
                "{brand} Pet Food - {weight}kg",
            ]
        }

        # Enforce brand -> category compatibility so we don't get nonsense
        # pairings like a beverage brand appearing as a spice brand.
        # If a category is not present here, brands will be chosen from the
        # overall brand list as a fallback.
        self.brand_category_map = {
            "Fresh Fruits": ["Local Vendor", "Organic Farms"],
            "Fresh Vegetables": ["Local Vendor", "Organic Farms"],
            "Pulses & Lentils": ["Tata Sampann", "Aashirvaad", "MTR" , "Local Vendor"],
            "Rice & Grains": ["India Gate", "KRBL (Daawat)", "Tilda"],
            "Atta & Flours": ["Aashirvaad", "Fortune"],
            "Spices & Masalas": ["MDH", "Everest", "Catch", "Badshah"],
            "Oils & Ghee": ["Fortune", "Dhara", "Saffola"],
            "Dairy & Eggs": ["Amul", "Mother Dairy", "Gowardhan", "Aavin"],
            "Tea & Coffee": ["Tata Tea", "Brooke Bond", "Bru Coffee"],
            "Snacks & Namkeen": ["Haldiram's", "Parle", "Bikano", "Lay's (India)", "Kurkure"],
            "Instant & Ready-to-Eat": ["Maggi", "MTR", "Gits"],
            "Pickles & Chutneys": ["Mother's Recipe", "Priya", "Dabur"],
            "Sweets & Mithai": ["Haldiram's", "Amul Mithai", "Lijjat"],
            "Beverages": ["Frooti", "Maaza", "Thums Up", "PepsiCo India", "Coca-Cola India"],
            "Bakery": ["Britannia", "Parle"],
            "Frozen Foods": ["McCain", "MTR", "ITC"],
            "Personal Care": ["Hindustan Unilever", "Dabur", "Himalaya", "Patanjali Ayurved", "Colgate-Palmolive India", "P&G India"],
            "Household & Cleaning": ["Hindustan Unilever", "Surf Excel", "Harpic", "Godrej Consumer"],
            "Baby & Kids": ["Pampers India", "Huggies", "Nestle India"],
            "Health & Wellness": ["Dabur", "Patanjali Ayurved", "Himalaya"],
            "Pet Care": ["Pedigree", "Drools", "Whiskas"]
        }
        
        # Product attributes (India-focused)
        self.fruits = ["Mango", "Banana", "Apple", "Guava", "Sapota", "Papaya", "Pomegranate", "Lychee", "Orange", "Lemon", "Jackfruit", "Custard Apple", "Sweet Lime", "Pear", "Grapes"]
        self.vegetables = ["Potato", "Onion", "Tomato", "Cabbage", "Cauliflower", "Spinach", "Brinjal", "Okra", "Bottle Gourd", "Bitter Gourd", "Carrot", "Radish", "Green Peas", "Drumstick", "Fenugreek"]
        self.dairy_products = ["Milk", "Ghee", "Paneer", "Curd", "Butter", "Khoa", "Flavored Milk"]
        self.meat_types = ["Chicken", "Mutton", "Fish", "Prawns", "Eggs"]
        self.beverage_types = ["Juice", "Soft Drink", "Lassi", "Buttermilk", "Tea", "Coffee", "Traditional Drink"]
        self.snack_types = ["Namkeen", "Chips", "Biscuits", "Samosa", "Vada", "Kachori", "Mixture", "Cookies", "Mixture", "Farsan"]
        self.pulses = ["Toor Dal", "Moong Dal", "Chana Dal", "Masoor Dal", "Urad Dal", "Rajma", "Chole"]
        self.rice_varieties = ["Basmati", "Sona Masuri", "Ponni", "Kolam", "Brown Rice"]
        self.spices = ["Turmeric", "Red Chilli", "Coriander Powder", "Cumin", "Mustard Seeds", "Fenugreek", "Garam Masala", "Curry Powder"]

        # Size variations
        self.sizes = ["Small", "Medium", "Large", "Extra Large", "Family Size", "Bulk", "Single Serve", "Travel Size"]
        self.varieties = ["Red", "Green", "Yellow", "Organic", "Conventional", "Local", "Premium", "Standard"]
        self.fat_contents = ["Whole", "2%", "1%", "Skim", "Low-Fat", "Non-Fat"]
        self.cuts = ["Breast", "Thigh", "Leg", "Wing", "Ground", "Chops", "Steak", "Roast", "Tenderloin"]

        # Aisle organization (simplified for Indian store)
        self.aisles = {
            "A": "Fresh Produce",
            "B": "Dairy & Eggs",
            "C": "Pulses & Grains",
            "D": "Spices & Oils",
            "E": "Snacks & Beverages",
            "F": "Bakery & Breakfast",
            "G": "Household & Cleaning",
            "H": "Personal Care",
            "I": "Frozen Foods & Ready-to-Eat",
            "J": "Baby & Kids",
        }

        # Bay and shelf organization
        self.bays = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        self.shelves = ["Top", "Middle", "Bottom", "Eye Level", "Lower"]
        self.positions = ["Left", "Center", "Right", "End Cap", "Display"]
    
    def generate_categories(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Insert categories and return mapping of name to ID."""
        cursor = conn.cursor()
        category_map = {}
        
        for category in self.categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, description, parent_category_id)
                VALUES (?, ?, ?)
            """, (category["name"], category["description"], None))
            
            category_id = cursor.lastrowid
            if category_id == 0:  # Already exists
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category["name"],))
                category_id = cursor.fetchone()[0]
            
            category_map[category["name"]] = category_id
        
        conn.commit()
        return category_map
    
    def generate_brands(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Insert brands and return mapping of name to ID."""
        cursor = conn.cursor()
        brand_map = {}
        
        for brand in self.brands:
            # Mark the majority of listed brands as India origin by default.
            country = "India"
            cursor.execute("""
                INSERT OR IGNORE INTO brands (name, description, country_of_origin)
                VALUES (?, ?, ?)
            """, (brand, f"{brand} brand products", country))
            
            brand_id = cursor.lastrowid
            if brand_id == 0:  # Already exists
                cursor.execute("SELECT id FROM brands WHERE name = ?", (brand,))
                brand_id = cursor.fetchone()[0]
            
            brand_map[brand] = brand_id
        
        conn.commit()
        return brand_map
    
    def generate_products(self, conn: sqlite3.Connection, category_map: Dict[str, int], brand_map: Dict[str, int], num_products: int = 1000) -> List[int]:
        """Generate products and return list of product IDs."""
        cursor = conn.cursor()
        product_ids = []
        
        # Category distribution weights
        category_weights = {
            "Fresh Fruits": 0.08, "Fresh Vegetables": 0.10, "Pulses & Lentils": 0.12,
            "Rice & Grains": 0.10, "Atta & Flours": 0.08, "Spices & Masalas": 0.10,
            "Oils & Ghee": 0.05, "Dairy & Eggs": 0.08, "Tea & Coffee": 0.04,
            "Snacks & Namkeen": 0.08, "Instant & Ready-to-Eat": 0.06, "Pickles & Chutneys": 0.02,
            "Sweets & Mithai": 0.01, "Beverages": 0.02, "Bakery": 0.02, "Frozen Foods": 0.01,
            "Personal Care": 0.01, "Household & Cleaning": 0.01, "Baby & Kids": 0.005, "Health & Wellness": 0.005, "Pet Care": 0.005
        }
        
        for i in range(num_products):
            # Select category based on weights
            category_name = random.choices(list(category_weights.keys()), weights=list(category_weights.values()))[0]
            category_id = category_map[category_name]
            
            # Select brand from the set appropriate for this category when possible
            allowed_brands = self.brand_category_map.get(category_name)
            if allowed_brands:
                # filter allowed brands to those present in brand_map (safety)
                allowed = [b for b in allowed_brands if b in brand_map]
                if allowed:
                    brand_name = random.choice(allowed)
                else:
                    brand_name = random.choice(self.brands)
            else:
                brand_name = random.choice(self.brands)
            brand_id = brand_map[brand_name]
            
            # Generate product name
            product_name = self._generate_product_name(category_name, brand_name)
            
            # Generate description
            description = self._generate_description(category_name, product_name)
            
            # Generate barcode (ensure uniqueness in DB)
            while True:
                barcode = self._generate_barcode()
                cursor.execute("SELECT 1 FROM products WHERE barcode = ?", (barcode,))
                if not cursor.fetchone():
                    break
            
            # Generate size and weight
            size = random.choice(self.sizes) if random.random() < 0.3 else None
            weight = f"{random.randint(1, 50)} {random.choice(['g', 'kg', 'ml', 'L'])}" if random.random() < 0.4 else None
            
            cursor.execute("""
                INSERT INTO products (name, brand_id, category_id, description, barcode, size, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_name, brand_id, category_id, description, barcode, size, weight))
            
            product_id = cursor.lastrowid
            product_ids.append(product_id)
        
        conn.commit()
        return product_ids
    
    def _generate_product_name(self, category_name: str, brand_name: str) -> str:
        """Generate realistic product name based on category."""
        if "Fruits" in category_name:
            fruit = random.choice(self.fruits)
            variety = random.choice(self.varieties)
            size = random.choice(self.sizes) if random.random() < 0.3 else ""
            return f"{brand_name} {variety} {fruit} {size}".strip()
        
        elif "Vegetables" in category_name:
            vegetable = random.choice(self.vegetables)
            variety = random.choice(self.varieties)
            size = random.choice(self.sizes) if random.random() < 0.3 else ""
            return f"{brand_name} {variety} {vegetable} {size}".strip()
        
        elif "Dairy" in category_name:
            dairy = random.choice(self.dairy_products)
            fat_content = random.choice(self.fat_contents) if random.random() < 0.4 else ""
            size = random.choice(self.sizes) if random.random() < 0.3 else ""
            return f"{brand_name} {fat_content} {dairy} {size}".strip()
        
        elif "Meat" in category_name or "Seafood" in category_name:
            meat = random.choice(self.meat_types)
            cut = random.choice(self.cuts) if random.random() < 0.3 else ""
            size = random.choice(self.sizes) if random.random() < 0.3 else ""
            return f"{brand_name} {cut} {meat} {size}".strip()
        
        elif "Beverages" in category_name:
            beverage = random.choice(self.beverage_types)
            flavor = random.choice(["Original", "Vanilla", "Chocolate", "Strawberry", "Orange", "Lemon", "Lime"])
            size = random.choice(self.sizes) if random.random() < 0.3 else ""
            return f"{brand_name} {flavor} {beverage} {size}".strip()
        
        elif "Snacks" in category_name:
            snack = random.choice(self.snack_types)
            flavor = random.choice(["Original", "BBQ", "Sour Cream", "Salt & Vinegar", "Cheddar", "Ranch"])
            size = random.choice(self.sizes) if random.random() < 0.3 else ""
            return f"{brand_name} {flavor} {snack} {size}".strip()
        
        else:
            # Generic product name
            generic_terms = ["Premium", "Classic", "Original", "Natural", "Organic", "Fresh", "Delicious"]
            term = random.choice(generic_terms)
            return f"{brand_name} {term} {category_name.split()[0]}"
    
    def _generate_description(self, category_name: str, product_name: str) -> str:
        """Generate product description."""
        descriptions = [
            f"High-quality {product_name.lower()} perfect for your family",
            f"Premium {product_name.lower()} made with the finest ingredients",
            f"Fresh {product_name.lower()} delivered to your table",
            f"Delicious {product_name.lower()} for everyday enjoyment",
            f"Natural {product_name.lower()} with no artificial preservatives",
            f"Organic {product_name.lower()} grown with care",
            f"Classic {product_name.lower()} that never goes out of style"
        ]
        return random.choice(descriptions)
    
    def _generate_barcode(self) -> str:
        """Generate realistic barcode."""
        return f"{random.randint(100000000000, 999999999999)}"
    
    def generate_locations(self, conn: sqlite3.Connection, product_ids: List[int]):
        """Generate inventory locations for products."""
        cursor = conn.cursor()
        
        for product_id in product_ids:
            # Get category for aisle assignment
            cursor.execute("""
                SELECT c.name FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE p.id = ?
            """, (product_id,))
            category_name = cursor.fetchone()[0]
            
            # Assign aisle based on category
            aisle = self._get_aisle_for_category(category_name)
            bay = random.choice(self.bays)
            shelf = random.choice(self.shelves)
            position = random.choice(self.positions)
            stock_level = random.randint(0, 100)
            
            cursor.execute("""
                INSERT INTO inventory_locations 
                (product_id, aisle, bay, shelf, position, stock_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, aisle, bay, shelf, position, stock_level))
        
        conn.commit()
    
    def _get_aisle_for_category(self, category_name: str) -> str:
        """Map category to appropriate aisle."""
        if "Fresh" in category_name or "Organic" in category_name:
            return "A"
        elif "Dairy" in category_name or "Eggs" in category_name:
            return "B"
        elif "Meat" in category_name or "Seafood" in category_name:
            return "C"
        elif "Frozen" in category_name:
            return "D"
        elif "Beverages" in category_name or "Water" in category_name:
            return "E"
        elif "Snacks" in category_name or "Candy" in category_name:
            return "F"
        elif "Grains" in category_name or "Canned" in category_name or "Condiments" in category_name:
            return "G"
        elif "Personal Care" in category_name or "Health" in category_name or "Baby" in category_name:
            return "H"
        elif "Cleaning" in category_name:
            return "I"
        elif "Pet" in category_name:
            return "J"
        else:
            return random.choice(list(self.aisles.keys()))
    
    def generate_synonyms(self, conn: sqlite3.Connection, product_ids: List[int]):
        """Generate synonyms and alternative names for products."""
        cursor = conn.cursor()
        
        # Common synonyms and abbreviations
        synonym_patterns = {
            "Milk": ["Dairy Milk", "Fresh Milk", "Whole Milk"],
            "Cheese": ["Cheese Product", "Dairy Cheese"],
            "Bread": ["Loaf", "Bread Loaf", "Fresh Bread"],
            "Chicken": ["Poultry", "Chicken Breast", "Chicken Thigh"],
            "Beef": ["Red Meat", "Beef Steak", "Ground Beef"],
            "Apple": ["Red Apple", "Green Apple", "Fresh Apple"],
            "Banana": ["Yellow Banana", "Fresh Banana"],
            "Orange": ["Orange Fruit", "Fresh Orange", "Citrus"],
            "Coca-Cola": ["Coke", "Cola", "Soft Drink"],
            "Pepsi": ["Pepsi Cola", "Cola Drink"],
            "Chips": ["Potato Chips", "Crisps", "Snack Chips"],
            "Cereal": ["Breakfast Cereal", "Morning Cereal"],
            "Yogurt": ["Greek Yogurt", "Dairy Yogurt", "Probiotic Yogurt"],
            "Water": ["Bottled Water", "Spring Water", "Purified Water"],
            "Coffee": ["Coffee Beans", "Ground Coffee", "Coffee Blend"],
            "Tea": ["Tea Bags", "Loose Tea", "Herbal Tea"],
            "Candy": ["Sweet Treat", "Confectionery", "Chocolate"],
            "Crackers": ["Snack Crackers", "Saltine Crackers"],
            "Nuts": ["Mixed Nuts", "Tree Nuts", "Roasted Nuts"],
            "Juice": ["Fruit Juice", "Fresh Juice", "100% Juice"]
        }
        
        for product_id in product_ids:
            # Get product name
            cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
            product_name = cursor.fetchone()[0]
            
            # Generate synonyms based on product name
            synonyms = []
            for pattern, alternatives in synonym_patterns.items():
                if pattern.lower() in product_name.lower():
                    synonyms.extend(alternatives[:random.randint(1, 3)])
            
            # Add generic synonyms
            if "Organic" in product_name:
                synonyms.append(product_name.replace("Organic", "").strip())
            if "Premium" in product_name:
                synonyms.append(product_name.replace("Premium", "").strip())
            if "Fresh" in product_name:
                synonyms.append(product_name.replace("Fresh", "").strip())
            
            # Add abbreviated versions
            words = product_name.split()
            if len(words) > 2:
                synonyms.append(" ".join(words[:2]))  # First two words
                synonyms.append(words[0])  # First word only
            
            # Insert synonyms
            for synonym in set(synonyms):  # Remove duplicates
                if synonym and synonym != product_name:
                    cursor.execute("""
                        INSERT INTO product_synonyms (product_id, synonym, synonym_type)
                        VALUES (?, ?, ?)
                    """, (product_id, synonym, "alternative_name"))
        
        conn.commit()
    
    def generate_keywords(self, conn: sqlite3.Connection, product_ids: List[int]):
        """Generate keywords for enhanced search."""
        cursor = conn.cursor()
        
        # Keyword categories
        dietary_keywords = ["Gluten-Free", "Dairy-Free", "Vegan", "Vegetarian", "Keto", "Low-Carb", "Sugar-Free", "Organic", "Non-GMO"]
        feature_keywords = ["Fresh", "Frozen", "Canned", "Dried", "Premium", "Classic", "Original", "Natural", "Artisan"]
        ingredient_keywords = ["Whole Grain", "Multi-Grain", "High Protein", "Low Sodium", "No Preservatives", "All Natural"]
        usage_keywords = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert", "Baking", "Cooking", "Grilling", "Salad"]
        
        for product_id in product_ids:
            # Get product details
            cursor.execute("""
                SELECT p.name, c.name as category, b.name as brand
                FROM products p
                JOIN categories c ON p.category_id = c.id
                JOIN brands b ON p.brand_id = b.id
                WHERE p.id = ?
            """, (product_id,))
            product_name, category, brand = cursor.fetchone()
            
            keywords = []
            
            # Add dietary keywords based on product characteristics
            if random.random() < 0.1:  # 10% chance
                keywords.append(random.choice(dietary_keywords))
            
            # Add feature keywords
            if random.random() < 0.2:  # 20% chance
                keywords.append(random.choice(feature_keywords))
            
            # Add ingredient keywords
            if random.random() < 0.15:  # 15% chance
                keywords.append(random.choice(ingredient_keywords))
            
            # Add usage keywords
            if random.random() < 0.25:  # 25% chance
                keywords.append(random.choice(usage_keywords))
            
            # Add category-specific keywords
            if "Fresh" in category:
                keywords.extend(["Fresh", "Local", "Seasonal"])
            elif "Organic" in category:
                keywords.extend(["Organic", "Natural", "Non-GMO"])
            elif "Frozen" in category:
                keywords.extend(["Frozen", "Quick", "Convenient"])
            
            # Insert keywords
            for keyword in set(keywords):
                cursor.execute("""
                    INSERT INTO product_keywords (product_id, keyword, keyword_type)
                    VALUES (?, ?, ?)
                """, (product_id, keyword, "feature"))
        
        conn.commit()
    
    def generate_popularity_data(self, conn: sqlite3.Connection, product_ids: List[int]):
        """Generate popularity scores and search data."""
        cursor = conn.cursor()
        
        for product_id in product_ids:
            search_count = random.randint(0, 1000)
            popularity_score = random.uniform(0.0, 1.0)
            last_searched = datetime.now() - timedelta(days=random.randint(0, 30))
            
            cursor.execute("""
                INSERT INTO product_popularity 
                (product_id, search_count, last_searched, popularity_score)
                VALUES (?, ?, ?, ?)
            """, (product_id, search_count, last_searched.isoformat(), popularity_score))
        
        conn.commit()
    
    def generate_database(self, db_path: str, num_products: int = 1000):
        """Generate complete database with all data."""
        print(f"Generating database with {num_products} products...")
        
    # Create database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Read and execute schema
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
            schema_sql = f.read()
        
        conn.executescript(schema_sql)
        print("+ Database schema created")
        
        # Generate data
        category_map = self.generate_categories(conn)
        print(f"+ Generated {len(category_map)} categories")
        
        brand_map = self.generate_brands(conn)
        print(f"+ Generated {len(brand_map)} brands")
        
        product_ids = self.generate_products(conn, category_map, brand_map, num_products)
        print(f"+ Generated {len(product_ids)} products")
        
        self.generate_locations(conn, product_ids)
        print("+ Generated inventory locations")
        
        self.generate_synonyms(conn, product_ids)
        print("+ Generated product synonyms")
        
        self.generate_keywords(conn, product_ids)
        print("+ Generated product keywords")
        
        self.generate_popularity_data(conn, product_ids)
        print("+ Generated popularity data")
        
        # Build vector embeddings and FAISS index (optional, requires sentence-transformers and faiss)
        try:
            print("+ Building embeddings and FAISS index (this may take a while)")
            import numpy as np
            # Compatibility shim: some versions of huggingface_hub removed
            # `cached_download` and provide `hf_hub_download` instead. The
            # sentence-transformers package (or its dependencies) may try to
            # import `cached_download` from huggingface_hub which raises
            # ImportError on newer hub versions. Monkeypatch the huggingface_hub
            # module to provide a `cached_download` alias when possible so the
            # rest of the pipeline can work without forcing a particular
            # huggingface_hub package version.
            try:
                import huggingface_hub as _hf_hub
                # Provide a compatibility wrapper for cached_download so
                # older callsites that pass url=... continue to work with
                # newer huggingface_hub that exposes hf_hub_download.
                if not hasattr(_hf_hub, 'cached_download') and hasattr(_hf_hub, 'hf_hub_download'):
                    def _cached_download(url=None, *args, **kwargs):
                        if url:
                            try:
                                import requests
                                import tempfile
                                import os
                                resp = requests.get(url, stream=True, timeout=30)
                                resp.raise_for_status()
                                filename = os.path.basename(url.split('?')[0]) or ''
                                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=filename)
                                for chunk in resp.iter_content(8192):
                                    if chunk:
                                        tmp.write(chunk)
                                tmp.close()
                                return tmp.name
                            except Exception:
                                return _hf_hub.hf_hub_download(*args, **kwargs)
                        return _hf_hub.hf_hub_download(*args, **kwargs)

                    _hf_hub.cached_download = _cached_download
            except Exception:
                # If we can't import or patch huggingface_hub, let the
                # downstream import raise and be caught by the outer except.
                pass

            from sentence_transformers import SentenceTransformer
            import faiss

            model = SentenceTransformer('all-MiniLM-L6-v2')

            cursor = conn.cursor()
            # Collect product textual context for embeddings
            cursor.execute("""
                SELECT p.id as product_id, p.name as product_name, b.name as brand_name,
                       c.name as category_name, p.description,
                       GROUP_CONCAT(DISTINCT ps.synonym) as synonyms,
                       GROUP_CONCAT(DISTINCT pk.keyword) as keywords
                FROM products p
                JOIN brands b ON p.brand_id = b.id
                JOIN categories c ON p.category_id = c.id
                LEFT JOIN product_synonyms ps ON p.id = ps.product_id
                LEFT JOIN product_keywords pk ON p.id = pk.product_id
                GROUP BY p.id
                ORDER BY p.id
            """)

            rows = cursor.fetchall()
            texts = []
            ids = []
            for row in rows:
                pid = row['product_id']
                parts = [row['product_name'] or '', row['brand_name'] or '', row['category_name'] or '', row['description'] or '']
                if row['synonyms']:
                    parts.append(row['synonyms'])
                if row['keywords']:
                    parts.append(row['keywords'])
                text = ' '.join([p for p in parts if p])
                texts.append(text)
                ids.append(pid)

            if texts:
                embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True, batch_size=64)
                # Normalize for cosine-similarity with inner product index
                faiss.normalize_L2(embeddings)

                d = embeddings.shape[1]
                index = faiss.IndexFlatIP(d)
                index.add(embeddings)

                data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
                os.makedirs(data_dir, exist_ok=True)
                index_path = os.path.join(data_dir, 'faiss_index.bin')
                faiss.write_index(index, index_path)

                # Store mapping table entries
                cursor.execute("DELETE FROM faiss_mapping")
                for idx, pid in enumerate(ids):
                    cursor.execute("INSERT INTO faiss_mapping (faiss_idx, product_id) VALUES (?, ?)", (idx, pid))
                conn.commit()
                print(f"+ FAISS index built and saved to {index_path}")
            else:
                print("+ No products available for embedding build")

        except Exception as e:
            print(f"! Skipped FAISS index build (missing packages or error): {e}")
        
        # Update FTS index
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products_fts(products_fts) VALUES('rebuild')
        """)
        print("+ Updated full-text search index")
        
        conn.commit()
        conn.close()
        
        print(f"+ Database generation complete: {db_path}")

def main():
    """Main function to generate the database."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Retail Shelf Assistant database')
    parser.add_argument('--products', type=int, default=1000, help='Number of products to generate')
    parser.add_argument('--output', type=str, default='../data/products.db', help='Output database path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible results')
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Generate database
    generator = ProductDataGenerator(seed=args.seed)
    generator.generate_database(args.output, args.products)
    
    print(f"\nDatabase generated successfully!")
    print(f"Products: {args.products}")
    print(f"Location: {args.output}")
    print(f"Seed: {args.seed}")

if __name__ == "__main__":
    main()
