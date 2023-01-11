import os
from .Data import *
from .Clustering import *
from .Solver import *
from .SolDrawer import *
import time
import datetime


def get_file_list(dataset_folder='Datasets\\golden-et-al-1998-set-1'):
    # Get the current working directory
    current_dir = os.getcwd()
    my_list = []

    # Walk through all the files and directories in the directory
    for dir_name, subdir_list, file_list in os.walk(current_dir):
        # Check if the current directory is the "Datasets" folder
        if dir_name == current_dir + '\\' + dataset_folder:
            # Loop through all the files in the "Datasets" folder
            for name in file_list:
                # Add the file to the list
                my_list.append(dataset_folder + '\\' + name)

    return my_list


def get_instance_name(file):
    # Split the file directory string into a list of levels
    levels = file.split(os.sep)

    # Get the last level
    instance_name = levels[-1]
    return instance_name


def solve_and_draw(instance_name, file, iterations=2000, limit=500, detailed_print=False):
    print('\n'+'='*100)
    print(f'Solving {file}...\n')
    # starting number of clusters (will probably change to create clusters of feasible demand)
    initial_number_of_clusters = 10

    # extract the data from the xml file and return number of nodes and vehicle capacity
    data = Data(file)
    number_of_nodes, vehicle_capacity = data.extract_data()
    avg_dem, std_dem = data.get_dem_stats()

    # convert the CVRP instance to a CluVRP instance
    cl = Clustering(data)
    num = cl.create_clusters(initial_number_of_clusters)
    if detailed_print:
        print(f'  Number of clusters for which the problem is solvable: {num}')

    # create the model of the problem (all classes, distance matrices)
    m = Model(cl, data)
    m.build_model()

    # initialize solver and solve the problem
    s = Solver(m)

    # get the solutions
    hard_solutions, hard_times = get_solutions(s, hard=True, iterations=iterations, limit=limit)
    soft_solutions, soft_times = get_solutions(s, hard=False, iterations=iterations, limit=limit)

    # draw solutions
    SolDrawer.draw_solutions(instance_name, hard=True, solutions=hard_solutions)
    SolDrawer.draw_solutions(instance_name, hard=False, solutions=soft_solutions)

    return number_of_nodes, vehicle_capacity, avg_dem, std_dem, hard_solutions, soft_solutions, hard_times, soft_times


def save_results(results):

    # Create a DataFrame from the nested dictionary
    results = pd.DataFrame.from_dict(results, orient='index')

    # Convert all values to numeric
    results = results.applymap(lambda x: pd.to_numeric(x, errors='coerce'))

    # round the values to 4 decimal places
    results = results.applymap(lambda x: round(x, 4))

    # Write the DataFrame to a CSV file
    results.to_csv('temp\\results.csv', index=False)

    # get current date and time
    now = datetime.datetime.now()

    # create the folder 'Plots_Results' if it doesn't already exist
    if not os.path.exists('Plots_Results'):
        os.makedirs('Plots_Results')

    # create a sub-folder named after the current date and time in the 'Plots_Results' folder
    date_time_folder = now.strftime('%Y-%m-%d %H-%M-%S')
    date_time_folder = date_time_folder.replace("-", "").replace(" ", "")
    if not os.path.exists(os.path.join('Plots_Results', date_time_folder)):
        os.makedirs(os.path.join('Plots_Results', date_time_folder))

    # move all files that begin with 'Golden' into the sub-folder
    for file in os.scandir('temp'):
        if file.name.startswith('Golden') or file.name.startswith('results'):
            os.rename(file.path, os.path.join('Plots_Results', date_time_folder, file.name))


def get_solutions(s, hard=True, detailed_print=False, iterations=2000, limit=500):
    # nearest neighbor vnd
    if hard:
        text = 'Hard-clustered'
    else:
        print('-' * 100+'\n')
        text = 'Soft-clustered'
    print(f'  {text} VND with Nearest Neighbor construction heuristic:')
    start_time = time.perf_counter()
    vnd_nn_solution = s.vnd(hard=hard, construction_method=0, detailed_print=detailed_print)
    end_time = time.perf_counter()
    vnd_nn_time = end_time - start_time

    # minimum insertions vnd
    if hard:
        text = 'Hard-clustered'
    else:
        text = 'Soft-clustered'
    print(f'  {text} VND with Minimum Insertions construction heuristic:')
    start_time = time.perf_counter()
    vnd_mi_solution = s.vnd(hard=hard, construction_method=1, detailed_print=detailed_print)
    end_time = time.perf_counter()
    vnd_mi_time = end_time - start_time

    # vns, initial solutions with nearest neighbor rcl algorithm, rcl length = 3
    if hard:
        text = 'Hard-clustered'
    else:
        text = 'Soft-clustered'
    print(f'  {text} VNS, initial solutions with nearest neighbor rcl algorithm (rcl length = 3):')
    start_time = time.perf_counter()
    vns_solution = s.vns(hard=hard, full_random_initial_solutions=False, iterations=iterations,
                         limit=limit, detailed_print=detailed_print)
    end_time = time.perf_counter()
    vns_time = end_time - start_time

    # store solutions and times
    solutions = (vnd_nn_solution, vnd_mi_solution, vns_solution)
    times = (vnd_nn_time, vnd_mi_time, vns_time)

    return solutions, times


def create_results_dictionary(results, instance_name, number_of_nodes, vehicle_capacity, avg_dem, std_dem,
                              hard_solutions, soft_solutions, hard_times, soft_times):
    # A = Hard-Clustered VND Nearest Neighbor, B = Hard-Clustered VND Minimum Insertions, C = Hard-Clustered VNS
    # D = Soft-Clustered VND Nearest Neighbor, E = Soft-Clustered VND Minimum Insertions, F = Soft-Clustered VNS
    results[instance_name] = {'Number of nodes': number_of_nodes, 'Vehicle Capacity': vehicle_capacity,
                              'Average node demand': avg_dem, 'St.Dev.': std_dem,
                              'A_Cost': hard_solutions[0][1].total_cost, 'A_Time': hard_times[0],
                              'B_Cost': hard_solutions[1][1].total_cost, 'B_Time': hard_times[1],
                              'C_Cost': hard_solutions[2][1].total_cost, 'C_Time': hard_times[2],
                              'D_Cost': soft_solutions[0][1].total_cost, 'D_Time': soft_times[0],
                              'E_Cost': soft_solutions[1][1].total_cost, 'E_Time': soft_times[1],
                              'F_Cost': soft_solutions[2][1].total_cost, 'F_Time': soft_times[2]
                              }
    return results
