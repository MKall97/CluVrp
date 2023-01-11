from SolverPackage import main_functions as mf
from PyInquirer import prompt

# set dataset directory
dataset_folder = 'Datasets\\golden-et-al-1998-set-1'

# get instances' list from dataset folder
file_list = mf.get_file_list(dataset_folder=dataset_folder)

# IF NOT USING IN CMD comment the below
questions = [
    {
        'type': 'list',
        'name': 'selected_option',
        'message': 'Please select an option:',
        'choices': file_list,
    }
]
answers = prompt(questions)
print(f"You selected {answers['selected_option']}")
file = answers['selected_option']

# IF NOT USING IN CMD uncomment the below
# file = 'Datasets\\golden-et-al-1998-set-1\\Golden_01.xml'

# initialize results dictionary
results = {}

# extract instance name
instance_name = mf.get_instance_name(file)

# solve and draw instance
number_of_nodes, vehicle_capacity, avg_dem, std_dem, hard_solutions, soft_solutions, hard_times, soft_times =\
    mf.solve_and_draw(instance_name, file, iterations=1000)

# Add the result to the dictionary
results = mf.create_results_dictionary(results, instance_name, number_of_nodes, vehicle_capacity, avg_dem,
                                       std_dem, hard_solutions, soft_solutions, hard_times, soft_times)

print('='*100)

# Save plots and results as a csv file
mf.save_results(results)
