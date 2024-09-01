import json
import uuid
import logging

# Set up logging
logging.basicConfig(
    filename="debug.log",  # Log file name
    level=logging.DEBUG,  # Minimum level of messages to log
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger()

# Data from the provided files
datacenters = {
    "DC1": {"cost_of_energy": 0.25, "slots_capacity": 25245},
    "DC2": {"cost_of_energy": 0.35, "slots_capacity": 15300},
    "DC3": {"cost_of_energy": 0.65, "slots_capacity": 7020},
    "DC4": {"cost_of_energy": 0.75, "slots_capacity": 8280},
}

# Server types and their active time steps and slots size
server_types = {
    "CPU.S1": {"type": "CPU", "active_range": range(1, 61), "slots_size": 2},
    "CPU.S2": {"type": "CPU", "active_range": range(37, 97), "slots_size": 2},
    "CPU.S3": {"type": "CPU", "active_range": range(73, 133), "slots_size": 2},
    "CPU.S4": {"type": "CPU", "active_range": range(109, 169), "slots_size": 2},
    "GPU.S1": {"type": "GPU", "active_range": range(1, 73), "slots_size": 4},
    "GPU.S2": {"type": "GPU", "active_range": range(49, 121), "slots_size": 4},
    "GPU.S3": {"type": "GPU", "active_range": range(97, 169), "slots_size": 4},
}

# Read the solution.json file
with open("solution.json") as f:
    solution_data = json.load(f)

actions = []
active_servers = {}  # Track active servers by (datacenter_id, server_type)
datacenter_usage = {dc: 0 for dc in datacenters}  # Track slots usage
previous_demands = {}


# Helper function to create unique server IDs
def generate_server_id():
    return str(uuid.uuid4())


# Helper function to check capacity constraint
def check_capacity(datacenter_id, slots_size, action):
    slots_capacity = datacenters[datacenter_id]["slots_capacity"]
    current_usage = datacenter_usage[datacenter_id]

    logger.debug(
        f"Checking capacity for action '{action}' on {datacenter_id}: "
        f"Current Usage = {current_usage}, Slots Size = {slots_size}, Capacity = {slots_capacity}"
    )

    if action == "buy":
        if current_usage + slots_size > slots_capacity:
            raise ValueError(
                f"Constraint 2 violated: {datacenter_id} capacity exceeded when trying to buy."
            )
    elif action == "dismiss":
        if current_usage - slots_size < 0:
            raise ValueError(
                f"Error: Negative slots usage encountered for {datacenter_id} when dismissing."
            )


# Loop through each time step and process actions
for time_step, demands in solution_data.items():
    time_step = int(time_step)
    logger.debug(f"Processing time step {time_step}...")
    for datacenter_id, servers in demands.items():
        for server_info in servers:
            for server_type, demand in server_info.items():
                if time_step in server_types[server_type]["active_range"]:
                    demand = int(demand)
                    prev_demand = int(
                        previous_demands.get((datacenter_id, server_type), 0)
                    )

                    logger.debug(
                        f"Time Step: {time_step}, Datacenter: {datacenter_id}, Server Type: {server_type}, "
                        f"Current Demand: {demand}, Previous Demand: {prev_demand}, Slots Used: {datacenter_usage[datacenter_id]}"
                    )

                    if (datacenter_id, server_type) not in active_servers:
                        active_servers[(datacenter_id, server_type)] = []

                    slots_size = server_types[server_type]["slots_size"]

                    if demand > prev_demand:
                        # Buy action
                        num_to_buy = min(
                            (demand - prev_demand),
                            (
                                datacenters[datacenter_id]["slots_capacity"]
                                - datacenter_usage[datacenter_id]
                            )
                            // slots_size,
                        )

                        for _ in range(num_to_buy):
                            check_capacity(datacenter_id, slots_size, "buy")
                            new_server_id = generate_server_id()
                            actions.append(
                                {
                                    "time_step": time_step,
                                    "datacenter_id": datacenter_id,
                                    "server_generation": server_type,
                                    "server_id": new_server_id,
                                    "action": "buy",
                                }
                            )
                            active_servers[(datacenter_id, server_type)].append(
                                new_server_id
                            )
                            datacenter_usage[datacenter_id] += slots_size

                    elif demand < prev_demand:
                        # Dismiss action
                        num_to_dismiss = min(
                            prev_demand - demand,
                            len(active_servers[(datacenter_id, server_type)]),
                        )
                        for _ in range(num_to_dismiss):
                            server_to_dismiss = active_servers[
                                (datacenter_id, server_type)
                            ].pop(0)
                            check_capacity(datacenter_id, slots_size, "dismiss")
                            actions.append(
                                {
                                    "time_step": time_step,
                                    "datacenter_id": datacenter_id,
                                    "server_generation": server_type,
                                    "server_id": server_to_dismiss,
                                    "action": "dismiss",
                                }
                            )
                            datacenter_usage[datacenter_id] -= slots_size

                    previous_demands[(datacenter_id, server_type)] = demand

                    # Log after processing
                    logger.debug(
                        f"After processing time step {time_step}, Datacenter {datacenter_id}: "
                        f"Slots Used = {datacenter_usage[datacenter_id]}, Remaining Capacity = {datacenters[datacenter_id]['slots_capacity'] - datacenter_usage[datacenter_id]}"
                    )

# Write the actions to a JSON file
with open("actions.json", "w") as f:
    json.dump(actions, f, indent=2)

logger.info("actions.json file generated successfully!")
