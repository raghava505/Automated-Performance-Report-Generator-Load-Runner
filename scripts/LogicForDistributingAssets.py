import numpy as np
from scipy.optimize import root_scalar
import math,json
# import sys

def softmax(x, base):
    """Custom softmax function with custom base."""
    e_x = base ** np.array(x)  # Exponentiate with the custom base
    y = list(e_x * 100 / e_x.sum(axis=0))
    # print(y)
    y= [0.0 if np.isnan(x) else x for x in y]
    return y


def find_optimal_exponent(customers, target_load_percentage, target_customer_ratio):
    if customers == 1:
        return 1
    # Indices defining the cut-off for the first target_customer_ratio percentage of customers
    cutoff_idx = math.floor(customers * target_customer_ratio)  # Cut-off index for the first X% customers
    customer_indices = list(range(1, customers + 1))
    # print("cutoff_idx : ",cutoff_idx)
    # Define the optimization target function
    def objective_function(base):
        y = softmax(customer_indices, base)  # Apply the softmax-like distribution with the given base
        first_customers_sum = sum(y[:cutoff_idx])  # Sum of the first X% customers' assigned load
        # print(f"Base : {base},  First {target_customer_ratio*100:.1f}% of customers sum: {first_customers_sum}")
        return first_customers_sum - target_load_percentage  # Difference between actual and desired

    # Solve for the root using numerical optimization
    result = root_scalar(
        objective_function, method='brentq', bracket=[0.1, 20]  # Adjusted bracket range
    )

    # If root finding fails, fallback to a reasonable default
    return result.root if result.converged else 1


def load_distribution(num_customers,first_x_customer_percentage,load_percentage_for_first_x_percent_customers):
    # Example Parameters
    # num_customers = 10  # Total number of customers
    # first_x_customer_percentage = 20  # Percentage of customers considered (first 10%)
    # load_percentage_for_first_x_percent_customers = 90  # Percentage of load we want on the first X customers
    x = list(range(1, num_customers + 1))
    if num_customers == 1:
        optimal_exponent = 1
        print(f"Distrituting all assets to a single customer.., optimal_exponent : {optimal_exponent}")
        return softmax(x, optimal_exponent)
    elif first_x_customer_percentage == load_percentage_for_first_x_percent_customers:
        optimal_exponent = 1
        print(f"Distrituting all assets uniformly.., optimal_exponent : {optimal_exponent}")
        return softmax(x, optimal_exponent)
    else:
        if math.floor(num_customers*first_x_customer_percentage/100)<1 :
            raise ValueError("Input error: first_x_customer_percentage should cover alteast 1 customer")
        if first_x_customer_percentage>90 or first_x_customer_percentage < 10:
            raise ValueError("first_x_customer_percentage value is too low or high. Please increase/decrease it and try again")
        if load_percentage_for_first_x_percent_customers>90 or load_percentage_for_first_x_percent_customers < 10:
            raise ValueError("load_percentage_for_first_x_percent_customers value is too low or high. Please increase/decrease it and try again")
        print(f"Finding optimal parameter to distribute {load_percentage_for_first_x_percent_customers}% assets to {first_x_customer_percentage}% of customers")
        # Dynamically compute optimal base for the desired parameters
        customer_ratio = first_x_customer_percentage/100
        optimal_exponent = find_optimal_exponent(num_customers,load_percentage_for_first_x_percent_customers,customer_ratio)
        # optimal_exponent = 1
        
        y = softmax(x, optimal_exponent)
        # print(y)
        print(f"Optimal Exponent Value to distribute assets in desired distribution is: {optimal_exponent}")
        print(f"First {customer_ratio*100:.1f}% of customers sum: {sum(y[:int(num_customers * customer_ratio)])}")

        # print(f"First value assigned: {y[0]}")
        return y

def adjust_allocation_to_match_total(current_segment_assets, initial_allocation):
    # Calculate the difference between the sum and total_assets
    difference = current_segment_assets - initial_allocation.sum()

    # Adjust the allocation
    if difference > 0:
        # Add 1 to some values to match the total
        for _ in range(difference):
            idx = np.argmin(initial_allocation)  # Add to the smallest values
            initial_allocation[idx] += 1
    elif difference < 0:
        # Subtract 1 from some values to match the total
        for _ in range(-difference):
            idx = np.argmax(initial_allocation)  # Subtract from the largest values
            initial_allocation[idx] -= 1

    # Ensure no value is zero
    initial_allocation[initial_allocation == 0] = 1

    # Final adjustment to maintain total assets
    while initial_allocation.sum() > current_segment_assets:
        idx = np.argmax(initial_allocation)
        initial_allocation[idx] -= 1

    return list(initial_allocation)

def return_asset_distribution(updated_test_input_params):
    return_dict = {}
    num_customers = updated_test_input_params["num_customers"]
    first_x_customer_percentage = updated_test_input_params["first_x_customer_percentage"]
    load_percentage_for_first_x_percent_customers = updated_test_input_params["load_percentage_for_first_x_percent_customers"]
    total_assets = updated_test_input_params["total_number_of_assets"]
    if num_customers>total_assets :
        raise ValueError("Error: num_customers is higher than total_assets. Each customer should get atleast one asset.")
    y = load_distribution(num_customers,first_x_customer_percentage,load_percentage_for_first_x_percent_customers)
    print("Converting percentage values into actual assets count...")
    initial_allocation = np.round(total_assets * np.array(y)/100).astype(int)
    cutoff_idx = math.floor(num_customers * first_x_customer_percentage/100)  # Cut-off index for the first X% customers

    print("Initial Allocation : ",initial_allocation)

    if num_customers >1 and (int(first_x_customer_percentage) != int(load_percentage_for_first_x_percent_customers) or (total_assets%num_customers)!=0):
        assets_to_enrol_for_each_customer_part1 = adjust_allocation_to_match_total(int(total_assets*load_percentage_for_first_x_percent_customers/100),initial_allocation[:cutoff_idx])
        assets_to_enrol_for_each_customer_part2 = adjust_allocation_to_match_total(int(total_assets*(100-load_percentage_for_first_x_percent_customers)/100),initial_allocation[cutoff_idx:])
        assets_to_enrol_for_each_customer = assets_to_enrol_for_each_customer_part1 + assets_to_enrol_for_each_customer_part2
        assets_to_enrol_for_each_customer = [int(value) for value in assets_to_enrol_for_each_customer]
    else:
        assets_to_enrol_for_each_customer = list(initial_allocation)
    if min(assets_to_enrol_for_each_customer) == 0:
        raise ValueError(f"{assets_to_enrol_for_each_customer.count(0)} customers are getting 0 assets. Each customer should get at least one asset allocated.")
    # print("Total assets to allocate to all customers : ",sum(assets_to_enrol_for_each_customer))
    # print("Total customers to allocate assets to : ",len(assets_to_enrol_for_each_customer))
    # print("Asset distribution : ",assets_to_enrol_for_each_customer)

    return_dict["1.Total assets to enroll"] = int(sum(assets_to_enrol_for_each_customer))
    return_dict["2.Total number of customers"] = len(assets_to_enrol_for_each_customer)
    return_dict["4.Asset Distribution for each customer"] = str(assets_to_enrol_for_each_customer)

    if num_customers>1:
        # print(f"First {first_x_customer_percentage:.1f}% of customers gets : {sum(assets_to_enrol_for_each_customer[:int(num_customers * first_x_customer_percentage/100)])} assets. ")
        # print(f"And The last {100-first_x_customer_percentage:.1f}% of customers gets : {sum(assets_to_enrol_for_each_customer)- sum(assets_to_enrol_for_each_customer[:int(num_customers * first_x_customer_percentage/100)])} assets. ")
        return_dict[f"5.First {first_x_customer_percentage:.1f}% ({int(num_customers * first_x_customer_percentage/100)}) of customers gets"] = f"{sum(assets_to_enrol_for_each_customer[:int(num_customers * first_x_customer_percentage/100)])} assets."
        return_dict[f"6.And The last {100-first_x_customer_percentage:.1f}% ({int(num_customers)-(int(num_customers * first_x_customer_percentage/100))}) of customers gets"] = f"{sum(assets_to_enrol_for_each_customer)- sum(assets_to_enrol_for_each_customer[:int(num_customers * first_x_customer_percentage/100)])} assets. "
    print(return_dict)
    return assets_to_enrol_for_each_customer,return_dict