import copy
import json
import os
import random
import subprocess
import tempfile
import concurrent.futures
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Pathing setup relative to workspace
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BOT_PATH = os.path.join(WORKSPACE_DIR, "bots", "parametric_bot")

@dataclass
class Genome:
    weights: Dict[str, float]
    fitness: float = -1.0

# Base parameters to use as template
BASE_WEIGHTS = {
    "spawn_ore_weight": 30.0,
    "spawn_proximity_weight": 20.0,
    "spawn_congestion_penalty": -6.0,
    "builder_early_game_cap": 3,      # integers should be mutated slightly differently, or treated as floats internally
    "builder_mid_game_cap": 5,
    "reserve_titanium": 30,
    "ore_repulsion_weight": 5.0
}

def generate_random_genome() -> Genome:
    """Generate a random variant of the base genome."""
    new_weights = {}
    for k, v in BASE_WEIGHTS.items():
        if isinstance(v, int):
            # Mutate int slightly around the base
            new_weights[k] = max(0, v + random.randint(-2, 2))
        else:
            # Mutate float slightly around the base
            new_weights[k] = v + random.uniform(-10.0, 10.0)
    return Genome(new_weights)

def mutate(genome: Genome) -> Genome:
    """Slightly modify a genome to search local parameter space."""
    new_weights = copy.deepcopy(genome.weights)
    
    # Pick a random gene to mutate
    gene_to_mutate = random.choice(list(new_weights.keys()))
    current_val = new_weights[gene_to_mutate]
    
    if isinstance(BASE_WEIGHTS[gene_to_mutate], int):
        new_weights[gene_to_mutate] = max(0, current_val + random.choice([-1, 1]))
    else:
        new_weights[gene_to_mutate] = current_val + random.uniform(-2.0, 2.0)
        
    return Genome(new_weights)

def crossover(parent1: Genome, parent2: Genome) -> Genome:
    """Combine genes from two parents."""
    new_weights = {}
    for k in BASE_WEIGHTS.keys():
        if random.random() < 0.5:
            new_weights[k] = parent1.weights[k]
        else:
            new_weights[k] = parent2.weights[k]
    return Genome(new_weights)

def evaluate_duel(genome_a: Genome, genome_b: Genome) -> Tuple[float, float]:
    """
    Runs cambc locally, pitting genome_a against genome_b.
    Returns (fitness_a, fitness_b).
    """
    
    # We need to temporarily write these to separate bot folders since cambc takes folder paths.
    # To avoid concurrency issues, we can create temporary folder copies.
    
    with tempfile.TemporaryDirectory() as dir_a, tempfile.TemporaryDirectory() as dir_b:
        # Setup Bot A
        os.system(f"cp -r {BOT_PATH}/* {dir_a}/")
        with open(os.path.join(dir_a, "weights.json"), "w") as f:
            json.dump(genome_a.weights, f)
            
        # Setup Bot B
        os.system(f"cp -r {BOT_PATH}/* {dir_b}/")
        with open(os.path.join(dir_b, "weights.json"), "w") as f:
            json.dump(genome_b.weights, f)
            
        # Run match 
        # Using subprocess to capture stderr (where our bots print FITNESS)
        cmd = ["cambc", "run", dir_a, dir_b]
        
        try:
             # Run cambc
             # Pass battlevenv binary implicitly if not activated, or assume it's run inside battlevenv
            process = subprocess.run(cmd, cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            print("Match timed out!")
            return (0.0, 0.0)

        # Parse output from stderr
        fit_a = 0.0
        fit_b = 0.0
        
        # Look for the FITNESS logs
        for line in process.stderr.splitlines():
            if line.startswith("FITNESS|"):
                parts = line.split("|")
                # e.g., FITNESS|Team.BLUE|350.0|TI:300|AX:0
                try:
                    team = parts[1]
                    fitness_val = float(parts[2])
                    # Assuming dir_a is Team.A and dir_b is Team.B (cambc default ordering)
                    if "Team.A" in team:
                        fit_a = fitness_val
                    elif "Team.B" in team:
                        fit_b = fitness_val
                except Exception as e:
                    pass
                    
        return fit_a, fit_b

def run_generation(population: List[Genome]) -> List[Genome]:
    """Evaluate population using parallel random pairings and tournament selection."""
    print("Evaluating generation (in parallel)...")
    # Reset fitness
    for g in population:
        g.fitness = 0.0

    # Simple 1v1 pairings
    random.shuffle(population)
    
    pairs = []
    # If odd, pair the last one with a random one from the existing population
    for i in range(0, len(population) - 1, 2):
        pairs.append((population[i], population[i+1]))
        
    if len(population) % 2 != 0:
        # Don't try to pop i+1, just explicitly pair the leftover bot
        pairs.append((population[-1], random.choice(population[0:-1])))

    def eval_worker(pair):
        u, v = pair
        fa, fb = evaluate_duel(u, v)
        return u, v, fa, fb

    # Run sub-processes in parallel
    current_matches = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(eval_worker, p) for p in pairs]
        
        for f in concurrent.futures.as_completed(futures):
            u, v, fa, fb = f.result()
            # In an odd population, a bot might play twice. Use max fitness.
            u.fitness = max(u.fitness, fa) if u.fitness > 0.1 else fa
            v.fitness = max(v.fitness, fb) if v.fitness > 0.1 else fb
            current_matches += 1
            print(f"Match {current_matches}/{len(pairs)} finished -> A: {fa:.1f}, B: {fb:.1f}")
        
    # Sort descending by fitness
    population.sort(key=lambda g: g.fitness, reverse=True)
    return population

def main():
    POPULATION_SIZE = 15
    GENERATIONS = 20
    
    # 1. Initialize random population (include default base as well)
    population = [Genome(BASE_WEIGHTS)] + [generate_random_genome() for _ in range(POPULATION_SIZE - 1)]
    
    for gen in range(GENERATIONS):
        print(f"\n=== GENERATION {gen+1} ===")
        # Evaluate
        population = run_generation(population)
        
        best = population[0]
        print(f"Best fitness this gen: {best.fitness:.1f}")
        print(f"Best weights: {best.weights}")
        
        # Write best to actual bot folder so it saves progress
        with open(os.path.join(BOT_PATH, "weights.json"), "w") as f:
            json.dump(best.weights, f, indent=2)

        # 2. Selection and Breed next generation
        next_gen = []
        # Keep top 2 directly (Elitism)
        next_gen.append(population[0])
        next_gen.append(population[1])
        
        # Breed the rest from top 50%
        top_half = population[:POPULATION_SIZE // 2]
        while len(next_gen) < POPULATION_SIZE:
            p1 = random.choice(top_half)
            p2 = random.choice(top_half)
            child = crossover(p1, p2)
            # 50% chance to mutate
            if random.random() < 0.5:
                child = mutate(child)
            next_gen.append(child)
            
        population = next_gen

if __name__ == "__main__":
    main()