import argparse
import pandas as pd
from tqdm import tqdm
from src.environment import HarbourEnv
from src.agents import UtilityAgentPolicy

def run_simulation(agent_type, seed):
    env = HarbourEnv(seed=seed)
    policy = UtilityAgentPolicy()  # ID 7 default parameters
    
    state = env.reset()
    done = False
    
    while not done:
        if agent_type == "utility":
            actions = policy.get_actions(state)
        else:
            actions = ["STAY"] * 5  # Baseline
            
        state, done = env.step(actions)
        
    return {
        "seed": seed,
        "delivered_cargo": state["delivered_cargo"],
        "crowding_violations": state["crowding_violations"],
        "storm_knockouts": state["storm_knockouts"]
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stormwatch Harbour Simulation (ID Ending in 7)")
    parser.add_argument("--agent", type=str, default="utility", choices=["do_nothing", "utility", "llm"])
    parser.add_argument("--seed", type=int, default=15)
    parser.add_argument("--eval_seeds", action="store_true", help="Run simulation across evaluation seeds 11 to 40")
    
    args = parser.parse_args()
    
    if args.eval_seeds:
        results = []
        print(f"Evaluating '{args.agent}' agent across 30 seeds (Seeds 11 to 40)...")
        for s in tqdm(range(11, 41)):
            res = run_simulation(args.agent, seed=s)
            results.append(res)
            
        df = pd.DataFrame(results)
        output_path = f"results/{args.agent}_eval_seeds_11_40.csv"
        df.to_csv(output_path, index=False)
        print(f"\nEvaluation complete. Results saved to '{output_path}'.")
        print("\nSummary Statistics:")
        print(df.describe())
    else:
        res = run_simulation(args.agent, seed=args.seed)
        print(f"\nSingle Simulation Run (Agent: {args.agent}, Seed: {args.seed}):")
        print(res)