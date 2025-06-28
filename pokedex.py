import requests
from fuzzywuzzy import process
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp

# Cache setup
CACHE_DIR = "pokemon_cache"
POKEMON_NAMES_CACHE_FILE = os.path.join(CACHE_DIR, "pokemon_names.json")
POKEMON_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "pokemon_data.json")
POKEMON_TYPES_CACHE_FILE = os.path.join(CACHE_DIR, "pokemon_types.json")

# Store pokemon names to avoid repeated API calls
POKEMON_NAMES_CACHE = None
POKEMON_DATA_CACHE = None
POKEMON_TYPES_CACHE = None

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
    if os.path.exists(POKEMON_TYPES_CACHE_FILE):
        os.remove(POKEMON_TYPES_CACHE_FILE)
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

def load_all_type_data():
    global POKEMON_TYPES_CACHE
    POKEMON_TYPES_CACHE = load_cache(POKEMON_TYPES_CACHE_FILE) or {}
    type_names = [
        "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
        "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"
    ]
    missing_types = [t for t in type_names if t not in POKEMON_TYPES_CACHE]
    if missing_types:
        for type_name in missing_types:
            try:
                response = requests.get(f"https://pokeapi.co/api/v2/type/{type_name}")
                if response.status_code == 200:
                    POKEMON_TYPES_CACHE[type_name] = response.json()
            except:
                pass
        save_cache(POKEMON_TYPES_CACHE_FILE, POKEMON_TYPES_CACHE)

def load_all_pokemon_data():
    global POKEMON_DATA_CACHE
    POKEMON_DATA_CACHE = load_cache(POKEMON_DATA_CACHE_FILE) or {}

def save_all_pokemon_data():
    global POKEMON_DATA_CACHE
    save_cache(POKEMON_DATA_CACHE_FILE, POKEMON_DATA_CACHE)

def get_pokemon_data(pokemon_name_or_id):
    global POKEMON_DATA_CACHE
    # Convert input to pokemon ID
    if str(pokemon_name_or_id).isdigit():
        pokemon_id = pokemon_name_or_id
    else:
        # Handle special forms
        if pokemon_name_or_id.lower().startswith('mega '):
            base_name = pokemon_name_or_id[5:].lower()
            closest_name = find_closest_pokemon_name(base_name)
            if closest_name:
                pokemon_id = f"mega-{closest_name}"
            else:
                pokemon_id = pokemon_name_or_id
        elif pokemon_name_or_id.lower().startswith('gigantamax ') or pokemon_name_or_id.lower().startswith('gmax '):
            base_name = pokemon_name_or_id.lower().replace('gigantamax ', '').replace('gmax ', '')
            closest_name = find_closest_pokemon_name(base_name)
            if closest_name:
                pokemon_id = f"gigantamax-{closest_name}"
            else:
                pokemon_id = pokemon_name_or_id
        elif any(pokemon_name_or_id.lower().startswith(prefix) for prefix in ['alolan ', 'galarian ', 'hisuian ', 'paldean ']):
            if pokemon_name_or_id.lower().startswith('alolan '):
                base_name = pokemon_name_or_id[7:].lower()
                variant = 'alola'
            elif pokemon_name_or_id.lower().startswith('galarian '):
                base_name = pokemon_name_or_id[9:].lower()
                variant = 'galar'
            elif pokemon_name_or_id.lower().startswith('hisuian '):
                base_name = pokemon_name_or_id[8:].lower()
                variant = 'hisui'
            elif pokemon_name_or_id.lower().startswith('paldean '):
                base_name = pokemon_name_or_id[8:].lower()
                variant = 'paldea'
            
            closest_name = find_closest_pokemon_name(base_name)
            if closest_name:
                pokemon_id = f"{closest_name}-{variant}"
            else:
                pokemon_id = pokemon_name_or_id
        else:
            closest_name = find_closest_pokemon_name(pokemon_name_or_id)
            if closest_name:
                pokemon_id = closest_name
            else:
                pokemon_id = pokemon_name_or_id

    # Check cache first (in-memory)
    if POKEMON_DATA_CACHE and str(pokemon_id).lower() in POKEMON_DATA_CACHE:
        return POKEMON_DATA_CACHE[str(pokemon_id).lower()], "cache"

    # Fetch from API if not in cache
    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id.lower()}")
        data = response.json()
        # Save to in-memory cache
        if POKEMON_DATA_CACHE is None:
            POKEMON_DATA_CACHE = {}
        POKEMON_DATA_CACHE[str(pokemon_id).lower()] = data
        return data, "api"
    except:
        return None, "error"

def get_type_data(type_url):
    global POKEMON_TYPES_CACHE
    type_name = type_url.split('/')[-2]
    if POKEMON_TYPES_CACHE and type_name in POKEMON_TYPES_CACHE:
        return POKEMON_TYPES_CACHE[type_name], "cache"
    # Fetch from API if not in cache
    try:
        response = requests.get(type_url)
        data = response.json()
        # Save to in-memory cache
        if POKEMON_TYPES_CACHE is None:
            POKEMON_TYPES_CACHE = {}
        POKEMON_TYPES_CACHE[type_name] = data
        save_cache(POKEMON_TYPES_CACHE_FILE, POKEMON_TYPES_CACHE)
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
    attack_type = "Either" if defense == sp_defense else "Physical" if defense < sp_defense else "Special"
    
    # Find type with highest damage multiplier
    best_type = None
    best_multiplier = 0
    
    # Track all immunities and worst types
    immunities = []
    worst_types = []
    worst_multiplier = 1
    
    for type_name, multiplier in damage_multipliers.items():
        if multiplier > best_multiplier:
            best_multiplier = multiplier
            best_type = type_name
        
        # Track immunities
        if multiplier == 0:
            immunities.append(type_name)
        
        # Track worst types (including immunities)
        if multiplier <= worst_multiplier:
            if multiplier < worst_multiplier:
                worst_types = []
                worst_multiplier = multiplier
            worst_types.append(type_name)
    
    return {
        'attack_category': attack_type,
        'best_type': best_type,
        'multiplier': best_multiplier,
        'immunities': immunities,
        'worst_types': worst_types,
        'worst_multiplier': worst_multiplier,
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
    
    # Handle mega searches
    if query.startswith('mega '):
        base_name = query[5:]  # Remove 'mega ' prefix
        # Search for base Pokémon that can mega evolve
        mega_capable = [
            'venusaur', 'charizard', 'blastoise', 'alakazam', 'gengar', 
            'kangaskhan', 'pinsir', 'gyarados', 'aerodactyl', 'mewtwo',
            'ampharos', 'scizor', 'heracross', 'houndoom', 'tyranitar',
            'blaziken', 'gardevoir', 'mawile', 'aggron', 'medicham',
            'manectric', 'banette', 'absol', 'garchomp', 'lucario',
            'abomasnow', 'beedrill', 'pidgeot', 'slowbro', 'steelix',
            'sceptile', 'swampert', 'sableye', 'sharpedo', 'camerupt',
            'altaria', 'glalie', 'salamence', 'metagross', 'latias',
            'latios', 'rayquaza', 'lopunny', 'gallade', 'audino',
            'diancie'
        ]
        
        for name in mega_capable:
            if base_name in name:
                results.append(f"mega-{name}")
    
    # Handle Gigantamax searches
    elif query.startswith('gigantamax ') or query.startswith('gmax '):
        base_name = query.replace('gigantamax ', '').replace('gmax ', '')
        # Search for base Pokémon that can Gigantamax
        gmax_capable = [
            'venusaur', 'charizard', 'blastoise', 'butterfree', 'pikachu',
            'meowth', 'machamp', 'gengar', 'kingler', 'lapras',
            'eevee', 'snorlax', 'garbodor', 'corviknight', 'orbeetle',
            'drednaw', 'coalossal', 'flapple', 'appletun', 'sandaconda',
            'toxtricity', 'centiskorch', 'hatterene', 'grimmsnarl',
            'alcremie', 'copperajah', 'duraludon', 'urshifu', 'calyrex'
        ]
        
        for name in gmax_capable:
            if base_name in name:
                results.append(f"gigantamax-{name}")
    
    # Handle regional variant searches
    elif any(query.startswith(prefix) for prefix in ['alolan ', 'galarian ', 'hisuian ', 'paldean ']):
        if query.startswith('alolan '):
            base_name = query[7:]
            variant = 'alola'
        elif query.startswith('galarian '):
            base_name = query[9:]
            variant = 'galar'
        elif query.startswith('hisuian '):
            base_name = query[8:]
            variant = 'hisui'
        elif query.startswith('paldean '):
            base_name = query[8:]
            variant = 'paldea'
        
        # Search for base Pokémon that have regional variants
        regional_variants = {
            'alola': ['rattata', 'raticate', 'raichu', 'sandshrew', 'sandslash', 
                     'vulpix', 'ninetales', 'diglett', 'dugtrio', 'meowth', 
                     'persian', 'geodude', 'graveler', 'golem', 'grimer', 
                     'muk', 'exeggutor', 'marowak', 'cubone', 'kangaskhan'],
            'galar': ['meowth', 'persian', 'ponyta', 'rapidash', 'farfetchd', 
                     'weezing', 'mr-mime', 'articuno', 'zapdos', 'moltres',
                     'slowpoke', 'slowbro', 'slowking', 'corsola', 'zigzagoon',
                     'linoone', 'darumaka', 'darmanitan', 'yamask', 'stunfisk',
                     'basculin', 'zorua', 'zoroark', 'tornadus', 'thundurus',
                     'landorus', 'enamorus'],
            'hisui': ['growlithe', 'arcanine', 'voltorb', 'electrode', 'typhlosion',
                     'qwilfish', 'sneasel', 'samurott', 'lilligant', 'basculin',
                     'zorua', 'zoroark', 'braviary', 'sliggoo', 'goodra',
                     'avalugg', 'decidueye'],
            'paldea': ['tauros', 'wooper', 'mimikyu']
        }
        
        if variant in regional_variants:
            for name in regional_variants[variant]:
                if base_name in name:
                    results.append(f"{name}-{variant}")
    else:
        # Regular search
        for name in pokemon_names:
            if query in name:
                results.append(name)
    
    return results, source

def display_pokemon_info(data, source):
    if not data:
        print("Pokemon not found")
        return

    # Display basic info with source
    print(f"\n--- {data['name'].upper()} ---")
    print(f"Data Source: {source.upper()}")
    print(f"ID: {data['id']}")

    types = [t['type']['name'] for t in data['types']]
    print(f"Types: {', '.join(types).title()}")

    # Display stats
    print("\nStats:")
    for stat in data['stats']:
        stat_name = stat['stat']['name'].replace('-', ' ').title()
        base_stat = stat['base_stat']
        print(f"  {stat_name}: {base_stat}")

    # Group type effectiveness
    print("\n--Damage Relationships--")

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

# Show attack recommendations
    attack_strategy = analyze_best_attack_strategy(data, damage_multipliers)
    
    print("\nRecommended Attack Strategy:")
    print(f"  Attack Category: {attack_strategy['attack_category']} (Defense: {attack_strategy['defense']}, Sp. Defense: {attack_strategy['sp_defense']})")
    if attack_strategy['best_type']:
        print(f"  Best Type: {attack_strategy['best_type'].title()} (Multiplier: {attack_strategy['multiplier']}x)")
    else:
        print("  No super-effective types found")
    
    # Display immunities if any
    if attack_strategy['immunities']:
        print(f"  Immunities: {', '.join(t.title() for t in sorted(attack_strategy['immunities']))}")
    
    # Display worst types
    if attack_strategy['worst_types']:
        worst_types_str = ', '.join(t.title() for t in sorted(attack_strategy['worst_types']))
        print(f"  Worst Types: {worst_types_str} (Multiplier: {attack_strategy['worst_multiplier']}x)")

def load_full_cache():
    print("Loading full Pokémon cache...")
    pokemon_names, source = get_all_pokemon_names()
    if not pokemon_names:
        print("Failed to load Pokémon names")
        return False
    
    total_pokemon = len(pokemon_names)
    print(f"Found {total_pokemon} Pokémon to cache")
    
    # Load cache data (in-memory)
    global POKEMON_DATA_CACHE
    if POKEMON_DATA_CACHE is None:
        POKEMON_DATA_CACHE = {}
    loaded = 0
    failed = 0

    async def fetch_and_store(session, name):
        url = f"https://pokeapi.co/api/v2/pokemon/{name}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return (name, data, True)
                else:
                    return (name, None, False)
        except Exception:
            return (name, None, False)

    async def fetch_all_pokemon():
        nonlocal loaded, failed
        connector = aiohttp.TCPConnector(limit=32)
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [fetch_and_store(session, name) for name in pokemon_names]
            for i, future in enumerate(asyncio.as_completed(tasks), 1):
                name, data, success = await future
                if success and data:
                    POKEMON_DATA_CACHE[name] = data
                    loaded += 1
                else:
                    failed += 1
                if i % 10 == 0:
                    print(f"Progress: {i}/{total_pokemon} Pokémon cached")

    asyncio.run(fetch_all_pokemon())
    
    # Save the updated cache once at the end
    save_all_pokemon_data()
    
    print(f"\nCache loading complete!")
    print(f"Successfully cached: {loaded} Pokémon")
    if failed > 0:
        print(f"Failed to cache: {failed} Pokémon")
    return True

def main():
    print("Pokédex - Offline Capable")
    print("Cache directory:", CACHE_DIR)
    print("\nCommands:")
    print("  search <query> - Search for Pokémon by name or type")
    print("  load          - Preload the cache with all Pokémon data")
    print("  clear         - Clear the cache")
    print("  quit          - Exit the program")
    
    # Load caches into memory at startup
    load_all_type_data()
    load_all_pokemon_data()
    
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
                
            # Check for load command
            if pokemon_input.lower() == 'load':
                load_full_cache()
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