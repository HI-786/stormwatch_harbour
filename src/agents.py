class UtilityAgentPolicy:
    def __init__(self, w1=3.0, w2=1.0, w3=2.0, w4=1000.0):
        self.w1 = w1  # Cargo weight
        self.w2 = w2  # Distance weight
        self.w3 = w3  # Crowding weight
        self.w4 = w4  # Storm risk weight

    def evaluate_utility(self, berth_id, env_state, worker_pos):
        ship = env_state["berth_ships"][berth_id]
        cargo = ship["cargo_remaining"]
        
        if cargo == 0 or ship["ship_id"] is None:
            return -9999.0

        # Disqualify B2 and B3 during storm warnings (ID ending in 7 rule)
        if env_state["storm_warning"] and berth_id in ["B2", "B3"]:
            return -9999.0

        bx, by = env_state["berths"][berth_id]
        dist = abs(worker_pos[0] - bx) + abs(worker_pos[1] - by)
        crowd = sum(1 for w in env_state["workers"] if w["assigned_berth"] == berth_id)
        
        return (self.w1 * cargo) - (self.w2 * dist) - (self.w3 * crowd)

    def get_actions(self, env_state):
        actions = []
        planned_occupancy = {}

        for w in env_state["workers"]:
            planned_occupancy[w["pos"]] = planned_occupancy.get(w["pos"], 0) + 1

        for worker in env_state["workers"]:
            wx, wy = worker["pos"]
            planned_occupancy[(wx, wy)] -= 1
            
            # Cancel B2/B3 assignments during storm warning
            if env_state["storm_warning"] and worker["assigned_berth"] in ["B2", "B3"]:
                worker["assigned_berth"] = None

            # Determine destination target
            if worker["cargo"] > 0:
                tx, ty = env_state["warehouse"]
                worker["assigned_berth"] = None
            else:
                best_berth = max(
                    env_state["berths"].keys(),
                    key=lambda b: self.evaluate_utility(b, env_state, worker["pos"])
                )
                
                if self.evaluate_utility(best_berth, env_state, worker["pos"]) < -500:
                    tx, ty = env_state["warehouse"]
                    worker["assigned_berth"] = None
                else:
                    worker["assigned_berth"] = best_berth
                    tx, ty = env_state["berths"][best_berth]

            # Primary movement vector
            dx, dy = 0, 0
            if wx < tx: dx = 1
            elif wx > tx: dx = -1
            elif wy < ty: dy = 1
            elif wy > ty: dy = -1

            next_x, next_y = wx + dx, wy + dy

            # Storm Safety Override: detour away from B2 (7,0) and B3 (12,0) cells during storms
            if env_state["storm_warning"] and (next_x, next_y) in [(7, 0), (12, 0)]:
                next_x, next_y = wx, min(11, wy + 1)

            # Crowding Avoidance (Max 3 workers per cell)
            if planned_occupancy.get((next_x, next_y), 0) >= 3:
                next_x, next_y = wx, wy

            planned_occupancy[(next_x, next_y)] = planned_occupancy.get((next_x, next_y), 0) + 1

            if next_x > wx: actions.append("RIGHT")
            elif next_x < wx: actions.append("LEFT")
            elif next_y > wy: actions.append("DOWN")
            elif next_y < wy: actions.append("UP")
            else: actions.append("STAY")
            
        return actions