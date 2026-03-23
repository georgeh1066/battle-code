import re

with open("tools/ga/trainer.py", "r") as f:
    data = f.read()

old = r'''def run_generation\(population: List\[Genome\]\) -> List\[Genome\]:.*?return population'''

new = '''def run_generation(population: List[Genome]) -> List[Genome]:
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
    return population'''

data = re.sub(old, new, data, flags=re.DOTALL)

with open("tools/ga/trainer.py", "w") as f:
    f.write(data)
