import json
from pulp import LpMaximize, LpProblem, LpVariable, LpStatus
from utils import load_json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
file_handler = logging.FileHandler('solution.log')
formatter = logging.Formatter(
    '%(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(file_handler)


def solve_by_latency_sensitivity(demand):
    # high
    high_result = maximize_profit_per_timestep(
        'high', demand['high demand'], 15300, 0.7)
    # medium
    medium_result = maximize_profit_per_timestep(
        'medium', demand['medium demand'], 15300, 0.35)
    # low
    low_result = maximize_profit_per_timestep(
        'low', demand['low demand'], 25245, 0.25)
    return {'high': high_result, 'medium': medium_result, 'low': low_result}


def get_server_details(server_generation):
    return load_json('servers.json').get(server_generation)


def maximize_profit_per_timestep(latency_sensitivity, servers_and_demands: dict, slot_capacity, energy_cost):

    prob = LpProblem("Maximize_Profit", LpMaximize)

    server_details = {}
    # Define decision variables
    decision_variables = {}
    for server in servers_and_demands.keys():
        decision_variables[server] = LpVariable(
            server, lowBound=0, cat='Integer')
        server_details[server] = (get_server_details(server))

    # Objective function components
    total_revenue = 0
    total_cost = 0

    for server, details in server_details.items():
        capacity = details["capacity"]
        energy_consumption = details["energy_consumption"]
        avg_maintenance_cost = details["avg_maintenance_cost"]
        selling_price = details["selling_price"][latency_sensitivity]

        # Calculate revenue and cost
        total_revenue += selling_price * capacity * decision_variables[server]
        total_cost += (energy_consumption * energy_cost +
                       avg_maintenance_cost) * decision_variables[server]

    # Add the objective function: Maximize profit
    prob += total_revenue - total_cost, "Total Profit"

    # Demand constraints
    for server, demand in servers_and_demands.items():
        capacity = server_details[server]['capacity']
        number_of_servers = decision_variables[server]
        prob += capacity * number_of_servers <= demand

    # Slot capacity constraint
    total_slot_usage = sum(details["slot_size"] * decision_variables[server]
                           for server, details in server_details.items())
    prob += total_slot_usage <= slot_capacity, "Slot Capacity"

    # Solve the problem
    prob.solve()

    # Print the results
    print("Status:", LpStatus[prob.status])
    results = {}
    for server in server_details:
        results[server] = {
            'Number of servers': decision_variables[server].varValue,
            'Demand met': server_details[server]["capacity"] * decision_variables[server].varValue if decision_variables[server].varValue else 0,
            'Revenue generated': server_details[server]["selling_price"]["medium"] * server_details[server]["capacity"] * decision_variables[server].varValue if decision_variables[server].varValue else 0,
            'Cost incurred': (server_details[server]["energy_consumption"] * 0.35 + server_details[server]["avg_maintenance_cost"]) * decision_variables[server].varValue if decision_variables[server].varValue else 0
        }

    # total_revenue = sum(details['Revenue generated']
    #                     for details in results.values())
    # total_cost = sum(details['Cost incurred'] for details in results.values())
    # total_profit = total_revenue - total_cost

    # Print the detailed results
    output = []
    for server, details in results.items():
        output.append({server: details['Number of servers']})

    #     print(f"Server {server}:")
    #     print(f"  Number of servers: {details['Number of servers']}")
    #     print(f"  Demand met: {details['Demand met']}")
    #     print(f"  Revenue generated: ${details['Revenue generated']:.2f}")
    #     print(f"  Cost incurred: ${details['Cost incurred']:.2f}")

    # print(f"Total revenue: ${total_revenue:.2f}")
    # print(f"Total cost: ${total_cost:.2f}")
    # print(f"Total profit: ${total_profit:.2f}")
    return output


if __name__ == "__main__":
    demands = load_json('demand_by_time_step_and_latency_sensitivity.json')
    solution = {}
    for demand in demands:
        timestep_solution = solve_by_latency_sensitivity(demand)
        solution[demand['time_step']] = timestep_solution

    with open('solution.json', 'w') as file:
        json.dump(solution, file, indent=4)
