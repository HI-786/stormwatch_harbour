import numpy as np

class HarbourEnv:
    def __init__(self, seed=42):
        self.width = 20
        self.height = 12
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        
        # Grid Coordinates
        self.warehouse = (10, 6)
        self.berths = {
            "B1": (2, 0),
            "B2": (7, 0),   # Unsafe during storm for ID ending in 7
            "B3": (12, 0),  # Unsafe during storm for ID ending in 7
            "B4": (17, 0)
        }
        self.reset()

    def reset(self):
        self.tick = 0
        self.max_ticks = 600
        
        self.workers = [
            {"id": i, "pos": (10, 6), "cargo": 0, "assigned_berth": None} 
            for i in range(5)
        ]
        
        self.berth_ships = {
            b: {"cargo_remaining": 0, "ship_id": None, "wait_ticks": 0} 
            for b in self.berths
        }
        
        self.storm_warning = False
        self.storm_active_berths = []
        self.delivered_cargo = 0
        self.crowding_violations = 0
        self.storm_knockouts = 0
        
        self._spawn_ships()
        return self.get_state()

    def _spawn_ships(self):
        for b in self.berths:
            if self.berth_ships[b]["ship_id"] is None and self.rng.random() < 0.35:
                self.berth_ships[b] = {
                    "ship_id": f"S-{self.tick}-{b}",
                    "cargo_remaining": int(self.rng.integers(15, 35)),
                    "wait_ticks": 0
                }

    def step(self, worker_actions):
        self.tick += 1
        
        # 1. Storm Warning Cycles (20 ticks warning every 50 ticks)
        if self.tick % 50 == 0:
            self.storm_warning = True
            self.storm_active_berths = ["B2", "B3"]
        elif self.tick % 50 == 20:
            self.storm_warning = False
            self.storm_active_berths = []

        # 2. Process Worker Movement
        cell_counts = {}
        for w_idx, action in enumerate(worker_actions):
            pos = list(self.workers[w_idx]["pos"])
            
            if action == "UP": pos[1] = max(0, pos[1] - 1)
            elif action == "DOWN": pos[1] = min(self.height - 1, pos[1] + 1)
            elif action == "LEFT": pos[0] = max(0, pos[0] - 1)
            elif action == "RIGHT": pos[0] = min(self.width - 1, pos[0] + 1)
            
            self.workers[w_idx]["pos"] = tuple(pos)
            cell_counts[tuple(pos)] = cell_counts.get(tuple(pos), 0) + 1

        # 3. Violations & Safety Checks
        for count in cell_counts.values():
            if count > 3:
                self.crowding_violations += 1

        if self.storm_warning:
            for w in self.workers:
                for unsafe_b in self.storm_active_berths:
                    if w["pos"] == self.berths[unsafe_b]:
                        self.storm_knockouts += 1

        # 4. Cargo Delivery & Pick Up
        for w in self.workers:
            # Drop off at warehouse
            if w["pos"] == self.warehouse and w["cargo"] > 0:
                self.delivered_cargo += w["cargo"]
                w["cargo"] = 0
            
            # Pick up cargo at berth
            if w["assigned_berth"]:
                b_pos = self.berths[w["assigned_berth"]]
                ship = self.berth_ships[w["assigned_berth"]]
                if w["pos"] == b_pos and ship["cargo_remaining"] > 0 and w["cargo"] == 0:
                    w["cargo"] = 1
                    ship["cargo_remaining"] -= 1

        # 5. Ship Queue Updates
        for b, ship in self.berth_ships.items():
            if ship["ship_id"]:
                ship["wait_ticks"] += 1
                if ship["cargo_remaining"] == 0:
                    self.berth_ships[b] = {"cargo_remaining": 0, "ship_id": None, "wait_ticks": 0}
                    
        self._spawn_ships()
        return self.get_state(), self.tick >= self.max_ticks

    def get_state(self):
        return {
            "tick": self.tick,
            "warehouse": self.warehouse,
            "workers": self.workers,
            "berths": self.berths,
            "berth_ships": self.berth_ships,
            "storm_warning": self.storm_warning,
            "storm_active_berths": self.storm_active_berths,
            "delivered_cargo": self.delivered_cargo,
            "crowding_violations": self.crowding_violations,
            "storm_knockouts": self.storm_knockouts
        }