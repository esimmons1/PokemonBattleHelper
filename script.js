class Pokedex {
    constructor() {
        this.baseUrl = 'https://pokeapi.co/api/v2';
        this.cache = new Map();
        this.typeCache = new Map();
        this.allPokemon = [];
        this.init();
    }

    async init() {
        console.log('Initializing Pokédex...');
        await this.loadAllPokemon();
        this.setupEventListeners();
        this.showWelcomeMessage();
    }

    async loadAllPokemon() {
        try {
            const response = await fetch(`${this.baseUrl}/pokemon?limit=1000`);
            const data = await response.json();
            this.allPokemon = data.results.map(pokemon => pokemon.name);
            console.log(`Loaded ${this.allPokemon.length} Pokémon names`);
        } catch (error) {
            console.error('Failed to load Pokémon list:', error);
        }
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        const searchInput = document.getElementById('pokemonSearch');
        const searchBtn = document.getElementById('searchBtn');
        const randomBtn = document.getElementById('randomBtn');
        const typeFilter = document.getElementById('typeFilter');

        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.searchPokemon());
        }
        
        if (randomBtn) {
            randomBtn.addEventListener('click', () => this.getRandomPokemon());
        }
        
        if (typeFilter) {
            typeFilter.addEventListener('change', () => this.handleTypeFilter());
        }

        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchPokemon();
                }
            });

            // Auto-search as user types
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        this.searchPokemonByName(query);
                    }, 300);
                } else {
                    this.hideAllResults();
                }
            });
        }
        
        console.log('Event listeners set up successfully');
    }

    showWelcomeMessage() {
        this.hideAllResults();
        const welcomeDiv = document.getElementById('welcomeMessage');
        if (welcomeDiv) {
            welcomeDiv.classList.remove('hidden');
            welcomeDiv.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <h2>Welcome to the Pokédex!</h2>
                    <p>Search for any Pokémon by name or ID to see detailed information including:</p>
                    <ul style="text-align: left; max-width: 400px; margin: 20px auto;">
                        <li>Base stats and type information</li>
                        <li>Type effectiveness (weaknesses, resistances, immunities)</li>
                        <li>Battle strategy recommendations</li>
                        <li>Support for Mega, Gigantamax, and regional forms</li>
                    </ul>
                    <p>Try searching for \"pikachu\", \"25\", or click \"Random\" to get started!</p>
                </div>
            `;
        }
    }

    async searchPokemon() {
        const searchInput = document.getElementById('pokemonSearch');
        const query = searchInput ? searchInput.value.trim() : '';
        
        console.log('Searching for:', query);
        
        if (!query) {
            this.showError('Please enter a Pokémon name or ID');
            return;
        }

        this.showLoading();
        
        try {
            const pokemonData = await this.getPokemonData(query);
            console.log('Pokemon data received:', pokemonData ? pokemonData.name : 'null');
            
            if (pokemonData) {
                await this.displayPokemonInfo(pokemonData);
            } else {
                this.showError('Pokémon not found. Please try a different name or ID.');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('An error occurred while fetching Pokémon data.');
        }
    }

    async searchPokemonByName(query) {
        if (query.length < 2) return;

        const results = this.allPokemon.filter(name => 
            name.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 20); // Limit to 20 results

        if (results.length > 0) {
            this.displaySearchResults(results);
        } else {
            this.hideAllResults();
        }
    }

    async getRandomPokemon() {
        const randomId = Math.floor(Math.random() * 1008) + 1; // Up to Gen 9
        const searchInput = document.getElementById('pokemonSearch');
        if (searchInput) {
            searchInput.value = randomId.toString();
        }
        await this.searchPokemon();
    }

    async getPokemonData(identifier) {
        // Check cache first
        const cacheKey = identifier.toLowerCase();
        if (this.cache.has(cacheKey)) {
            console.log('Using cached data for:', identifier);
            return this.cache.get(cacheKey);
        }

        console.log('Fetching data for:', identifier);
        
        try {
            const response = await fetch(`${this.baseUrl}/pokemon/${identifier.toLowerCase()}`);
            console.log('API response status:', response.status);
            
            if (!response.ok) {
                console.log('API response not ok:', response.status, response.statusText);
                return null;
            }
            
            const data = await response.json();
            console.log('Data fetched successfully:', data.name);
            this.cache.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Error fetching Pokémon data:', error);
            return null;
        }
    }

    async getTypeData(typeUrl) {
        if (this.typeCache.has(typeUrl)) {
            return this.typeCache.get(typeUrl);
        }

        try {
            const response = await fetch(typeUrl);
            const data = await response.json();
            this.typeCache.set(typeUrl, data);
            return data;
        } catch (error) {
            console.error('Error fetching type data:', error);
            return null;
        }
    }

    async displayPokemonInfo(pokemonData) {
        console.log('Displaying Pokémon info for:', pokemonData.name);
        this.hideAllResults();
        
        const pokemonInfo = document.getElementById('pokemonInfo');
        if (!pokemonInfo) {
            console.error('Pokemon info container not found');
            return;
        }
        
        pokemonInfo.classList.remove('hidden');

        // Basic info
        const nameElement = document.getElementById('pokemonName');
        const idElement = document.getElementById('pokemonId');
        const spriteElement = document.getElementById('pokemonSprite');
        
        if (nameElement) nameElement.textContent = pokemonData.name.charAt(0).toUpperCase() + pokemonData.name.slice(1);
        if (idElement) idElement.textContent = `#${pokemonData.id.toString().padStart(3, '0')}`;
        if (spriteElement) spriteElement.src = pokemonData.sprites.front_default;

        // Types
        const typesContainer = document.getElementById('pokemonTypes');
        if (typesContainer) {
            typesContainer.innerHTML = '';
            pokemonData.types.forEach(type => {
                const typeBadge = document.createElement('div');
                typeBadge.className = 'type-badge';
                typeBadge.textContent = type.type.name;
                typesContainer.appendChild(typeBadge);
            });
        }

        // Stats
        this.displayStats(pokemonData.stats);

        // Type effectiveness
        const typeEffectivenessData = await this.displayTypeEffectiveness(pokemonData.types);

        // Battle strategy
        await this.displayBattleStrategy(pokemonData, typeEffectivenessData);
    }

    displayStats(stats) {
        const statsContainer = document.getElementById('pokemonStats');
        if (!statsContainer) return;
        
        statsContainer.innerHTML = '';

        const statNames = {
            'hp': 'HP',
            'attack': 'Attack',
            'defense': 'Defense',
            'special-attack': 'Sp. Atk',
            'special-defense': 'Sp. Def',
            'speed': 'Speed'
        };

        stats.forEach(stat => {
            const statItem = document.createElement('div');
            statItem.className = 'stat-item';
            statItem.innerHTML = `
                <span class="stat-name">${statNames[stat.stat.name]}</span>
                <span class="stat-value">${stat.base_stat}</span>
            `;
            statsContainer.appendChild(statItem);
        });
    }

    async displayTypeEffectiveness(types) {
        const weaknesses = [];
        const resistances = [];
        const immunities = [];
        const damageMultipliers = {};

        // Calculate type effectiveness
        for (const type of types) {
            const typeData = await this.getTypeData(type.type.url);
            if (typeData) {
                // Double damage from
                typeData.damage_relations.double_damage_from.forEach(damageType => {
                    const typeName = damageType.name;
                    damageMultipliers[typeName] = (damageMultipliers[typeName] || 1) * 2;
                });

                // Half damage from
                typeData.damage_relations.half_damage_from.forEach(damageType => {
                    const typeName = damageType.name;
                    damageMultipliers[typeName] = (damageMultipliers[typeName] || 1) * 0.5;
                });

                // No damage from
                typeData.damage_relations.no_damage_from.forEach(damageType => {
                    const typeName = damageType.name;
                    damageMultipliers[typeName] = 0;
                });
            }
        }

        // Categorize types
        Object.entries(damageMultipliers).forEach(([typeName, multiplier]) => {
            if (multiplier >= 4) {
                weaknesses.push({ type: typeName, multiplier: 4 });
            } else if (multiplier >= 2) {
                weaknesses.push({ type: typeName, multiplier: 2 });
            } else if (multiplier === 0) {
                immunities.push({ type: typeName, multiplier: 0 });
            } else if (multiplier <= 0.25) {
                resistances.push({ type: typeName, multiplier: 0.25 });
            } else if (multiplier <= 0.5) {
                resistances.push({ type: typeName, multiplier: 0.5 });
            }
        });

        // Display weaknesses
        const weaknessesContainer = document.getElementById('weaknesses');
        if (weaknessesContainer) {
            weaknessesContainer.innerHTML = '';
            if (weaknesses.length > 0) {
                weaknesses.forEach(weakness => {
                    const item = document.createElement('div');
                    item.className = 'effectiveness-item';
                    item.innerHTML = `
                        <span>${weakness.type.charAt(0).toUpperCase() + weakness.type.slice(1)}</span>
                        <span class="multiplier">${weakness.multiplier}x</span>
                    `;
                    weaknessesContainer.appendChild(item);
                });
            } else {
                weaknessesContainer.innerHTML = '<p>None</p>';
            }
        }

        // Display resistances
        const resistancesContainer = document.getElementById('resistances');
        if (resistancesContainer) {
            resistancesContainer.innerHTML = '';
            if (resistances.length > 0) {
                resistances.forEach(resistance => {
                    const item = document.createElement('div');
                    item.className = 'effectiveness-item';
                    item.innerHTML = `
                        <span>${resistance.type.charAt(0).toUpperCase() + resistance.type.slice(1)}</span>
                        <span class="multiplier">${resistance.multiplier}x</span>
                    `;
                    resistancesContainer.appendChild(item);
                });
            } else {
                resistancesContainer.innerHTML = '<p>None</p>';
            }
        }

        // Display immunities
        const immunitiesContainer = document.getElementById('immunities');
        if (immunitiesContainer) {
            immunitiesContainer.innerHTML = '';
            if (immunities.length > 0) {
                immunities.forEach(immunity => {
                    const item = document.createElement('div');
                    item.className = 'effectiveness-item';
                    item.innerHTML = `
                        <span>${immunity.type.charAt(0).toUpperCase() + immunity.type.slice(1)}</span>
                        <span class="multiplier">Immune</span>
                    `;
                    immunitiesContainer.appendChild(item);
                });
            } else {
                immunitiesContainer.innerHTML = '<p>None</p>';
            }
        }

        // Return the type effectiveness data for use in battle strategy
        return { weaknesses, resistances, immunities };
    }

    async displayBattleStrategy(pokemonData, typeEffectivenessData) {
        const strategyContainer = document.getElementById('battleStrategy');
        if (!strategyContainer) return;
        
        strategyContainer.innerHTML = '';

        // Get all stats
        let hp = 0, attack = 0, defense = 0, spAttack = 0, spDefense = 0, speed = 0;
        pokemonData.stats.forEach(stat => {
            if (stat.stat.name === 'hp') hp = stat.base_stat;
            if (stat.stat.name === 'attack') attack = stat.base_stat;
            if (stat.stat.name === 'defense') defense = stat.base_stat;
            if (stat.stat.name === 'special-attack') spAttack = stat.base_stat;
            if (stat.stat.name === 'special-defense') spDefense = stat.base_stat;
            if (stat.stat.name === 'speed') speed = stat.base_stat;
        });

        // Get type effectiveness data from parameter
        const weaknesses = typeEffectivenessData.weaknesses;
        const resistances = typeEffectivenessData.resistances;
        const immunities = typeEffectivenessData.immunities;

        // Determine best attack category to use against this Pokémon
        const bestAttackCategory = defense === spDefense ? 'Either' : 
                                 defense < spDefense ? 'Physical' : 'Special';

        // Determine what this Pokémon is good at attacking with
        const isPhysicalAttacker = attack > spAttack + 20;
        const isSpecialAttacker = spAttack > attack + 20;
        const isMixedAttacker = Math.abs(attack - spAttack) <= 20;

        // Create strategy content
        let strategyHTML = '';

        // Best way to attack this Pokémon
        strategyHTML += '<div class="strategy-item">';
        strategyHTML += '<strong>Best Attack Strategy Against This Pokémon:</strong><br>';
        strategyHTML += `- Use <strong>${bestAttackCategory.toLowerCase()}</strong> attacks for maximum damage<br>`;
        strategyHTML += `- Defense: ${defense} | Sp. Defense: ${spDefense}<br>`;
        strategyHTML += '</div>';

        // What to watch out for from this Pokémon
        strategyHTML += '<div class="strategy-item">';
        strategyHTML += '<strong>What This Pokémon Can Do To You:</strong><br>';
        
        if (isPhysicalAttacker) {
            strategyHTML += `- <span style="color: #e74c3c;">⚠️ Strong physical attacker (Attack: ${attack})</span><br>`;
            strategyHTML += '- Watch out for powerful physical moves<br>';
        } else if (isSpecialAttacker) {
            strategyHTML += `- <span style="color: #e74c3c;">⚠️ Strong special attacker (Sp. Atk: ${spAttack})</span><br>`;
            strategyHTML += '- Watch out for powerful special moves<br>';
        } else {
            strategyHTML += `- Balanced attacker (Atk: ${attack}, Sp. Atk: ${spAttack})<br>`;
            strategyHTML += '- Can hit hard with both physical and special moves<br>';
        }
        strategyHTML += '</div>';

        // Type-specific counter strategies
        strategyHTML += '<div class="strategy-item">';
        strategyHTML += '<strong>Type Counter Strategy:</strong><br>';
        
        if (weaknesses.length > 0) {
            const weaknessTypes = weaknesses.map(w => w.type.charAt(0).toUpperCase() + w.type.slice(1)).join(', ');
            strategyHTML += `- <span style="color: #27ae60;">Use ${weaknessTypes} moves for super effective damage</span><br>`;
            strategyHTML += '   - These types will deal 2x or 4x damage<br>';
        }
        
        if (immunities.length > 0) {
            const immunityTypes = immunities.map(i => i.type.charAt(0).toUpperCase() + i.type.slice(1)).join(', ');
            strategyHTML += `- <span style="color: #e74c3c;">Avoid ${immunityTypes} moves - they won\'t work</span><br>`;
            strategyHTML += '   - These types cannot damage this Pokémon at all<br>';
        }
        
        if (resistances.length > 0) {
            const resistanceTypes = resistances.map(r => r.type.charAt(0).toUpperCase() + r.type.slice(1)).join(', ');
            strategyHTML += `- <span style="color: #e74c3c;">Avoid ${resistanceTypes} moves - they\'ll be weak</span><br>`;
            strategyHTML += '   - These types deal reduced damage<br>';
        }
        
        if (weaknesses.length === 0 && immunities.length === 0 && resistances.length === 0) {
            strategyHTML += '- No significant type advantages or disadvantages<br>';
        }
        strategyHTML += '</div>';

        // Special counter strategies
        if (immunities.length > 0) {
            strategyHTML += '<div class="strategy-item">';
            strategyHTML += '<strong>Special Counter Notes:</strong><br>';
            strategyHTML += '- This Pokémon has type immunities - plan your moves carefully<br>';
            strategyHTML += '- Consider moves that can hit normally immune types (e.g., Foresight + Normal moves)<br>';
            strategyHTML += '</div>';
        }

        // HP-based counter strategies
        if (hp < 50) {
            strategyHTML += '<div class="strategy-item">';
            strategyHTML += '<strong>Fragile Target:</strong><br>';
            strategyHTML += `- Very low HP (${hp}) - easy to knock out<br>`;
            strategyHTML += '- Any strong hit will likely defeat it<br>';
            strategyHTML += '- Priority moves can finish it off quickly<br>';
            strategyHTML += '</div>';
        } else if (hp > 120) {
            strategyHTML += '<div class="strategy-item">';
            strategyHTML += '<strong>Tanky Target:</strong><br>';
            strategyHTML += `- High HP (${hp}) - will take many hits to defeat<br>`;
            strategyHTML += '- Use your strongest moves or status effects<br>';
            strategyHTML += '- Consider moves that ignore defense or cause status<br>';
            strategyHTML += '</div>';
        }

        // Speed-based counter strategies
        if (speed > 100) {
            strategyHTML += '<div class="strategy-item">';
            strategyHTML += '<strong>Fast Opponent:</strong><br>';
            strategyHTML += `- High Speed (${speed}) - will likely attack first<br>`;
            strategyHTML += '- Use priority moves to hit before it attacks<br>';
            strategyHTML += '- Consider defensive strategies or switching<br>';
            strategyHTML += '</div>';
        } else if (speed < 50) {
            strategyHTML += '<div class="strategy-item">';
            strategyHTML += '<strong>Slow Opponent:</strong><br>';
            strategyHTML += `- Low Speed (${speed}) - you\'ll likely attack first<br>`;
            strategyHTML += '- Take advantage of going first to deal damage<br>';
            strategyHTML += '- Consider setup moves before attacking<br>';
            strategyHTML += '</div>';
        }

        // Overall threat assessment
        const totalStats = hp + attack + defense + spAttack + spDefense + speed;
        const averageStat = totalStats / 6;
        
        strategyHTML += '<div class="strategy-item">';
        strategyHTML += '<strong>Threat Assessment:</strong><br>';
        if (averageStat > 100) {
            strategyHTML += `- <span style="color: #e74c3c;">High threat level (avg stats: ${Math.round(averageStat)})</span><br>`;
            strategyHTML += '- Bring your strongest counters<br>';
        } else if (averageStat < 70) {
            strategyHTML += `- <span style="color: #27ae60;">Low threat level (avg stats: ${Math.round(averageStat)})</span><br>`;
            strategyHTML += '- Should be easy to handle<br>';
        } else {
            strategyHTML += `- <span style="color: #f39c12;">Moderate threat level (avg stats: ${Math.round(averageStat)})</span><br>`;
            strategyHTML += '- Use appropriate counters<br>';
        }
        strategyHTML += '</div>';

        strategyContainer.innerHTML = strategyHTML;
    }

    displaySearchResults(results) {
        this.hideAllResults();
        
        const searchResults = document.getElementById('searchResults');
        const resultsList = document.getElementById('resultsList');
        
        if (!searchResults || !resultsList) return;
        
        searchResults.classList.remove('hidden');
        resultsList.innerHTML = '';

        results.forEach(pokemonName => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.textContent = pokemonName.charAt(0).toUpperCase() + pokemonName.slice(1);
            resultItem.addEventListener('click', () => {
                const searchInput = document.getElementById('pokemonSearch');
                if (searchInput) {
                    searchInput.value = pokemonName;
                }
                this.searchPokemon();
            });
            resultsList.appendChild(resultItem);
        });
    }

    handleTypeFilter() {
        const typeFilter = document.getElementById('typeFilter');
        const selectedType = typeFilter ? typeFilter.value : '';
        
        if (!selectedType) {
            this.hideAllResults();
            this.showWelcomeMessage();
            return;
        }

        // Filter Pokémon by type
        this.filterPokemonByType(selectedType);
    }

    async filterPokemonByType(type) {
        this.showLoading();
        
        try {
            const response = await fetch(`${this.baseUrl}/type/${type}`);
            const typeData = await response.json();
            
            const pokemonOfType = typeData.pokemon.map(p => p.pokemon.name);
            this.displaySearchResults(pokemonOfType);
        } catch (error) {
            this.showError('Failed to filter Pokémon by type.');
        }
    }

    showLoading() {
        this.hideAllResults();
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
        }
    }

    showError(message) {
        this.hideAllResults();
        const errorElement = document.getElementById('error');
        if (errorElement) {
            const errorText = errorElement.querySelector('p');
            if (errorText) {
                errorText.textContent = message;
            }
            errorElement.classList.remove('hidden');
        }
    }

    hideAllResults() {
        const loadingElement = document.getElementById('loading');
        const errorElement = document.getElementById('error');
        const pokemonInfoElement = document.getElementById('pokemonInfo');
        const searchResultsElement = document.getElementById('searchResults');
        const welcomeDiv = document.getElementById('welcomeMessage');
        
        if (loadingElement) loadingElement.classList.add('hidden');
        if (errorElement) errorElement.classList.add('hidden');
        if (pokemonInfoElement) pokemonInfoElement.classList.add('hidden');
        if (searchResultsElement) searchResultsElement.classList.add('hidden');
        if (welcomeDiv) welcomeDiv.classList.add('hidden');
    }
}

// Initialize the Pokédex when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Pokédex...');
    new Pokedex();
});

// Also add a fallback in case DOMContentLoaded already fired
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, initializing Pokédex...');
        new Pokedex();
    });
} else {
    console.log('DOM already loaded, initializing Pokédex immediately...');
    new Pokedex();
} 