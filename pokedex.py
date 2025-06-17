import requests
from fuzzywuzzy import process
import json
import os

# Cache setup
CACHE_DIR = "pokemon_cache"
POKEMON_NAMES_CACHE_FILE = os.path.join(CACHE_DIR, "pokemon_names.json")
POKEMON_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "pokemon_data.json")

# Store pokemon names to avoid repeated API calls
POKEMON_NAMES_CACHE = None

def ensure_cache_dir():
    # Create cache directory if missing
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_cache(file_path):
    # Load data from cache file
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_cache(file_path, data):
    # Save data to cache file
    ensure_cache_dir()
    with open(file_path, 'w') as f:
        json.dump(data, f)

def clear_cache():
    # Clear all cache files
    if os.path.exists(POKEMON_NAMES_CACHE_FILE):
        os.remove(POKEMON_NAMES_CACHE_FILE)
    if os.path.exists(POKEMON_DATA_CACHE_FILE):
        os.remove(POKEMON_DATA_CACHE_FILE)
    print("Cache cleared")

def get_all_pokemon_names():
    global POKEMON_NAMES_CACHE
    
    # Load from cache first
    if POKEMON_NAMES_CACHE is None:
        cache_data = load_cache(POKEMON_NAMES_CACHE_FILE)
        if cache_data:
            POKEMON_NAMES_CACHE = cache_data
            return POKEMON_NAMES_CACHE, "cache"

    # Fetch from API if cache missing
    try:
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1000")
        data = response.json()
        POKEMON_NAMES_CACHE = [pokemon['name'] for pokemon in data['results']]
        save_cache(POKEMON_NAMES_CACHE_FILE, POKEMON_NAMES_CACHE)
        return POKEMON_NAMES_CACHE, "api"
    except:
        if POKEMON_NAMES_CACHE is None:
            cache_data = load_cache(POKEMON_NAMES_CACHE_FILE)
            if cache_data:
                print("Using cached list")
                POKEMON_NAMES_CACHE = cache_data
                return POKEMON_NAMES_CACHE, "cache"
            else:
                return [], "error"
    return POKEMON_NAMES_CACHE, "cache"

def find_closest_pokemon_name(input_name):
    # Find closest matching pokemon name using fuzzy matching
    pokemon_names, _ = get_all_pokemon_names()
    if not pokemon_names:
        return None
    
    # Check exact match first
    if input_name.lower() in pokemon_names:
        return input_name.lower()
    
    # Use fuzzy matching for close matches
    result = process.extractOne(input_name.lower(), pokemon_names)
    if result and result[1] >= 80:
        return result[0]
    return None

def get_pokemon_data(pokemon_name_or_id):
    # Convert input to pokemon ID
    if str(pokemon_name_or_id).isdigit():
        pokemon_id = pokemon_name_or_id
    else:
        closest_name = find_closest_pokemon_name(pokemon_name_or_id)
        if closest_name:
            pokemon_id = closest_name
        else:
            pokemon_id = pokemon_name_or_id

    # Check cache first
    cache_data = load_cache(POKEMON_DATA_CACHE_FILE)
    if cache_data and str(pokemon_id).lower() in cache_data:
        return cache_data[str(pokemon_id).lower()], "cache"

    # Fetch from API if not in cache
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id.lower()}")
        data = response.json()
        
        # Save to cache
        if cache_data is None:
            cache_data = {}
        cache_data[str(pokemon_id).lower()] = data
        save_cache(POKEMON_DATA_CACHE_FILE, cache_data)
        
        return data, "api"
    except:
        return None, "error"

def get_type_data(type_url):
    # Extract type name from URL
    type_name = type_url.split('/')[-2]
    
    # Check cache first
    cache_data = load_cache(POKEMON_DATA_CACHE_FILE)
    if cache_data and f"type_{type_name}" in cache_data:
        return cache_data[f"type_{type_name}"], "cache"

    # Fetch from API if not in cache
    try:
        response = requests.get(type_url)
        data = response.json()
        
        # Save to cache
        if cache_data is None:
            cache_data = {}
        cache_data[f"type_{type_name}"] = data
        save_cache(POKEMON_DATA_CACHE_FILE, cache_data)
        
        return data, "api"
    except:
        return None, "error"

def analyze_best_attack_strategy(data, damage_multipliers):
    # Get defense stats
    defense = 0
    sp_defense = 0
    for stat in data['stats']:
        if stat['stat']['name'] == 'defense':
            defense = stat['base_stat']
        if stat['stat']['name'] == 'special-defense':
            sp_defense = stat['base_stat']
    
    # Choose physical or special based on lower defense
    attack_type = "Physical" if defense < sp_defense else "Special"
    
    # Find type with highest damage multiplier
    best_type = None
    best_multiplier = 0
    
    for type_name, multiplier in damage_multipliers.items():
        if multiplier > best_multiplier:
            best_multiplier = multiplier
            best_type = type_name
    
    return {
        'attack_category': attack_type,
        'best_type': best_type,
        'multiplier': best_multiplier,
        'defense': defense,
        'sp_defense': sp_defense
    }

def search_pokemon(query):
    # Search for pokemon by name only (no type search)
    pokemon_names, source = get_all_pokemon_names()
    if not pokemon_names:
        return [], source

    results = []
    query = query.lower()
    
    # Search by name only
    for name in pokemon_names:
        if query in name:
            results.append(name)
    
    return results, source

def display_pokemon_info(data, source):
    if not data:
        print("Pokemon not found")
        return

    # Display basic info
    print(f"\n--- {data['name'].upper()} --- [Source: {source.upper()}]")
    print(f"ID: {data['id']}")

    types = [t['type']['name'] for t in data['types']]
    print(f"Types: {', '.join(types).title()}")

    # Display stats
    print("\nStats:")
    for stat in data['stats']:
        stat_name = stat['stat']['name'].replace('-', ' ').title()
        base_stat = stat['base_stat']
        print(f"  {stat_name}: {base_stat}")

    # Calculate type effectiveness
    damage_multipliers = {}
    for pokemon_type in data['types']:
        type_url = pokemon_type['type']['url']
        type_data, type_source = get_type_data(type_url)
        if type_data:
            # Calculate damage multipliers
            for damage_relation in type_data['damage_relations']['double_damage_from']:
                type_name = damage_relation['name']
                damage_multipliers[type_name] = damage_multipliers.get(type_name, 1) * 2
            
            for damage_relation in type_data['damage_relations']['half_damage_from']:
                type_name = damage_relation['name']
                damage_multipliers[type_name] = damage_multipliers.get(type_name, 1) * 0.5
            
            for damage_relation in type_data['damage_relations']['no_damage_from']:
                type_name = damage_relation['name']
                damage_multipliers[type_name] = 0

    # Show attack recommendations
    attack_strategy = analyze_best_attack_strategy(data, damage_multipliers)
    
    print("\nRecommended Attack Strategy:")
    print(f"  Attack Category: {attack_strategy['attack_category']} (Defense: {attack_strategy['defense']}, Sp. Defense: {attack_strategy['sp_defense']})")
    if attack_strategy['best_type']:
        print(f"  Best Type: {attack_strategy['best_type'].title()} (Multiplier: {attack_strategy['multiplier']}x)")
    else:
        print("  No super-effective types found")

    # Group type effectiveness
    print("\nDamage Relationships:")
    
    multiplier_groups = {
        4: [],
        2: [],
        1: [],
        0.5: [],
        0.25: [],
        0: []
    }
    
    # Sort types by effectiveness
    for type_name, multiplier in damage_multipliers.items():
        if multiplier >= 4:
            multiplier_groups[4].append(type_name)
        elif multiplier >= 2:
            multiplier_groups[2].append(type_name)
        elif multiplier <= 0:
            multiplier_groups[0].append(type_name)
        elif multiplier <= 0.25:
            multiplier_groups[0.25].append(type_name)
        elif multiplier <= 0.5:
            multiplier_groups[0.5].append(type_name)
        else:
            multiplier_groups[1].append(type_name)
    
    # Show weaknesses
    if multiplier_groups[4] or multiplier_groups[2]:
        print("\nWeaknesses:")
        if multiplier_groups[4]:
            print(f"  4x: {', '.join(sorted(multiplier_groups[4])).title()}")
        if multiplier_groups[2]:
            print(f"  2x: {', '.join(sorted(multiplier_groups[2])).title()}")
    
    # Show resistances
    if multiplier_groups[0] or multiplier_groups[0.25] or multiplier_groups[0.5]:
        print("\nResistances:")
        if multiplier_groups[0]:
            print(f"  Immune: {', '.join(sorted(multiplier_groups[0])).title()}")
        if multiplier_groups[0.25]:
            print(f"  1/4x: {', '.join(sorted(multiplier_groups[0.25])).title()}")
        if multiplier_groups[0.5]:
            print(f"  1/2x: {', '.join(sorted(multiplier_groups[0.5])).title()}")

def main():
    print("Pokédex - Offline Capable")
    print("Cache directory:", CACHE_DIR)
    print("\nCommands:")
    print("  search <query> - Search for Pokémon by name or type")
    print("  clear         - Clear the cache")
    print("  quit          - Exit the program")
    
    while True:
        try:
            pokemon_input = input("\nEnter Pokemon name or ID (or 'quit' to exit): ").strip()
            
            # Ignore file paths or suspicious input
            if any(x in pokemon_input for x in ['/', '\\', ':', '"', "'"]):
                print("Please enter a valid Pokémon name or ID, not a file path or command.")
                continue
            
            # Check for quit command
            if pokemon_input.lower() == 'quit':
                break
                
            # Check for clear command
            if pokemon_input.lower() == 'clear':
                clear_cache()
                continue
                
            # Check for search command
            if pokemon_input.lower().startswith('search '):
                query = pokemon_input[7:].strip()
                results, source = search_pokemon(query)
                if results:
                    print(f"\nFound {len(results)} Pokémon matching '{query}' [Source: {source.upper()}]:")
                    for name in sorted(results):
                        print(f"- {name.title()}")
                else:
                    print(f"No Pokémon found matching '{query}'")
                continue
                
            # Validate input
            if not pokemon_input:
                print("Please enter a valid Pokémon name or ID")
                continue
                
            # Remove any quotes or special characters
            pokemon_input = pokemon_input.strip('"\'')
            
            # Check for name corrections
            if not str(pokemon_input).isdigit():
                closest_name = find_closest_pokemon_name(pokemon_input)
                if closest_name and closest_name != pokemon_input.lower():
                    print(f"\nDid you mean: {closest_name.title()}?")
                    confirm = input("Press Enter to continue with this suggestion, or type 'no' to try again: ")
                    if confirm.lower() == 'no':
                        continue
                    pokemon_input = closest_name
            
            pokemon_data, source = get_pokemon_data(pokemon_input)
            if pokemon_data:
                display_pokemon_info(pokemon_data, source)
            else:
                print(f"Could not find Pokémon: {pokemon_input}")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again with a valid Pokémon name or ID")

if __name__ == "__main__":
    main()