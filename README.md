Pokémon Battle Helper
===============

Made by: Ellis Simmons - June 2025  
Languages: Python (requests, fuzzywuzzy, JSON, and file I/O)

What is this?
-------------
This is a command-line Pokédex app that lets you look up any Pokémon, even offline.  
It caches Pokémon data locally and gives you battle recommendations based on types and stats.
Although the cache does work offline it takes a while to upload everything. Will remove once fully updated

What it does:
-------------
- Looks up any Pokémon by name or ID.
- Suggests correct names if your input is close but not exact.
- Shows full stat breakdown, types, and weaknesses along with reccomended attack strategy.
- Groups damage relationships into multipliers (like 4x, 2x, immune, etc.).
- Tells you whether to use physical or special attacks.
- Identifies best and worst types to use against the Pokémon.
- Lets you preload or clear the entire cache.

How it works:
-------------
- Uses the PokéAPI (https://pokeapi.co) to fetch data.      
- Caches Pokémon data in JSON files to avoid repeated API calls. **Warning: Takes a long time**    
- Fuzzy matches names using `fuzzywuzzy` if you mistype.    
- Handles type effectiveness via damage relations and calculates the best attacking strategy.      

Commands supported:
-------------------
- `search <name>` – Search Pokémon by name fragment  
- `load` – Preload the entire Pokédex cache (all ~1000 Pokémon) **Again, Takes a long time**    
- `clear` – Clear all cache files  **Not reccomended, will need to reload for offline use again**
- `quit` – Exit the program  
- Entering any name or ID directly will show stats and suggestions.

How to use it:
------------------------
- Download the zip of the GitHub repo. 
- Install dependencies in terminal. 
- Navigate to the file location and run it. `python pokedex.py`   
- Load while you have internet to use when you don't. **Loading is not necessary to run** 

Why I made it:
--------------
I wanted a fast and offline-capable Pokédex tool I could run in the terminal without needing a browser.  
Plus it was a fun way to work with APIs, caching, CLI interfaces, and fuzzy matching logic.

Stuff you can tweak:
--------------------
- You can modify the cache system to expire after time.
- Easy to change how results are printed or logged.
- Could be extended with evolution chains, move data, or shiny sprites.
- Could also turn it into a Flask API or GUI app.

---
As usual, if you're going to use or modify it, credit me please. Have a nice day.
