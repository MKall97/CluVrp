from SolverPackage import main_functions as mf

# set dataset directory
dataset_folder = 'Datasets\\golden-et-al-1998-set-1'

# get instances' list from dataset folder
file_list = mf.get_file_list(dataset_folder=dataset_folder)

# initialize results dictionary
results = {}

# solve all instances
for i, file in enumerate(file_list):

    # extract instance name
    instance_name = mf.get_instance_name(file)

    # Remove the ".xml" extension, if it exists, to save the name of the instance
    # if it does not exist, skip the file
    if instance_name.endswith(".xml"):
        instance_name = instance_name[:-4]
    else:
        continue

    # solve and draw instance
    number_of_nodes, vehicle_capacity, avg_dem, std_dem, hard_solutions, soft_solutions, hard_times, soft_times =\
        mf.solve_and_draw(instance_name, file, iterations=1000)

    # Add the result to the dictionary
    results = mf.create_results_dictionary(results, instance_name, number_of_nodes, vehicle_capacity, avg_dem, std_dem,
                                           hard_solutions, soft_solutions, hard_times, soft_times)
    # uncomment the below to for first 5 instances
    # if i == 5:
    #     break

print('='*100)

# Save plots and results as a csv file
mf.save_results(results)
