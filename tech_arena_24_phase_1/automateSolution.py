import json
import uuid

# Data from the provided files
datacenters = {
    "low": {"datacenter_id": "DC1", "cost_of_energy": 0.25, "slots_capacity": 25245},
    "medium": {"datacenter_id": "DC2", "cost_of_energy": 0.35, "slots_capacity": 15300},
    "high": [
        {"datacenter_id": "DC3", "cost_of_energy": 0.65, "slots_capacity": 7020},
        {"datacenter_id": "DC4", "cost_of_energy": 0.75, "slots_capacity": 8280},
    ],
}

# Server types and their active time steps
server_types = {
    "CPU.S1": {"type": "CPU", "active_range": range(1, 61)},
    "CPU.S2": {"type": "CPU", "active_range": range(37, 97)},
    "CPU.S3": {"type": "CPU", "active_range": range(73, 133)},
    "CPU.S4": {"type": "CPU", "active_range": range(109, 169)},
    "GPU.S1": {"type": "GPU", "active_range": range(1, 73)},
    "GPU.S2": {"type": "GPU", "active_range": range(49, 121)},
    "GPU.S3": {"type": "GPU", "active_range": range(97, 169)},
}

# Read the solution.json file
with open("tech_arena_24_phase_1\solution.json") as f:
    solution_data = json.load(f)

actions = []
previous_demands = {}


# Helper function to create unique server IDs
def generate_server_id():
    return str(uuid.uuid4())


# Loop through each time step and process actions
for time_step, demands in solution_data.items():
    time_step = int(time_step)
    for latency, servers in demands.items():
        if latency == "high":
            # Alternate between DC3 and DC4 for high sensitivity
            datacenter_info = datacenters["high"][(time_step - 1) % 2]
        else:
            datacenter_info = datacenters[latency]

        datacenter_id = datacenter_info["datacenter_id"]

        for server_info in servers:
            for server_type, demand in server_info.items():
                if time_step in server_types[server_type]["active_range"]:
                    # Check previous demand to decide on buy or dismiss
                    prev_demand = previous_demands.get((latency, server_type), 0)
                    if demand > prev_demand:
                        # Buy action
                        for _ in range(demand - prev_demand):
                            actions.append(
                                {
                                    "time_step": time_step,
                                    "datacenter_id": datacenter_id,
                                    "server_generation": server_type,
                                    "server_id": generate_server_id(),
                                    "action": "buy",
                                }
                            )
                    elif demand < prev_demand:
                        # Dismiss action
                        for _ in range(prev_demand - demand):
                            actions.append(
                                {
                                    "time_step": time_step,
                                    "datacenter_id": datacenter_id,
                                    "server_generation": server_type,
                                    "server_id": generate_server_id(),
                                    "action": "dismiss",
                                }
                            )

                    # Update previous demand for next comparison
                    previous_demands[(latency, server_type)] = demand

# Write the actions to a JSON file
with open("actions.json", "w") as f:
    json.dump(actions, f, indent=2)

print("actions.json file generated successfully!")
