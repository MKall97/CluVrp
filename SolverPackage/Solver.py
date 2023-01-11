from .Vrp import *
from .Tsp import *
from .Optimisation import *
from tqdm import tqdm
from statistics import mean


class Solution:
    def __init__(self):
        self.total_cost = 0.0
        self.cost_per_route = []
        self.routes = []

    def back_up(self):
        cloned = Solution()
        cloned.routes = self.routes.copy()
        cloned.total_cost = self.total_cost
        cloned.cost_per_route = self.cost_per_route.copy()
        return cloned

    def __str__(self):
        print(f'  {len(self.routes)} Routes were created:')
        for i, route in enumerate(self.routes):
            print(f'      {i+1}. {[node.ID for node in route]}')
            print(f'          Cost: {round(self.cost_per_route[i],4)}\n')
        print(f'\n  Total Cost: {round(self.total_cost,4)}')
        print(f'  Average Route Cost: {round(mean(self.cost_per_route),4)}')
        return ''


class Solver:
    def __init__(self, m):
        self.m = m
        self.all_nodes = m.all_nodes
        self.depot = m.all_nodes[len(m.all_nodes)-1]
        self.distance_matrix = m.distance_matrix
        self.clusters = m.clusters
        self.cluster_routes = []
        self.hard = None
        self.construction_method = None
        self.length_of_rcl = None
        self.move_type = None
        self.optimisation_method = None
        self.total_cost = 0
        self.cost_per_route = []
        self.solution = Solution()
        self.optimised_solution = None

    def solve(self, hard=True, construction_method=0, length_of_rcl=1,
              optimisation_method=0, move_type=0):
        """

        :param hard: [True, False] default: True
        :param construction_method: [0: nearest neighbor, 1: minimum insertions, 2: random] | default: 0
        :param length_of_rcl: [any integer >= 0] | default: 1 (does not randomize solution) (works only with n.n.)
        :param optimisation_method: [0: local search, 1: VND, 2: VNS, 3: Taboo] | default: 0
        :param move_type: [0: Relocation, 1: Swap, 2: Two Opt] | default: 0 | works only with local search
        """
        # reset before each execution
        self.reset()
        self.hard = hard
        self.construction_method = construction_method
        self.length_of_rcl = length_of_rcl
        self.move_type = move_type
        self.optimisation_method = optimisation_method
        # solve the high level problem
        vrp = Vrp(self.m)
        vrp.clarke_wright(self.cluster_routes)  # to find cluster routes

        # solve the low level problem
        tsp = Tsp(self)
        tsp.construct_solution()

        # optimize the solution
        optimisation = Optimisation(self)
        self.optimised_solution = optimisation.optimise_solution()

        return self.solution, self.optimised_solution

    def reset(self):
        for node in self.all_nodes:
            if node.ID != self.depot.ID:
                node.is_routed = False
            node.neighbors = []
            node.cluster_route = None
        self.cluster_routes = []
        self.total_cost = 0
        self.cost_per_route = []
        self.solution = Solution()
        self.optimised_solution = None

    def check_solution(self, solution):
        all_routed = all([node.is_routed for node in self.all_nodes])
        cost_per_route_verification = []
        print(f'  All nodes routed: {all_routed}')
        if not all_routed:
            not_routed = [node.ID for node in self.all_nodes if not node.is_routed]
            print(f'  These nodes were not routed: {not_routed}')
        routes_set_list = []
        for route in solution.routes:
            routes_set_list.append(set([node.ID for node in route]))
        routes_intersection = set.intersection(*routes_set_list)
        if len(routes_intersection) == 1 and self.depot.ID in routes_intersection:
            pass
        else:
            print(f'  Some Nodes were not routed only once!'
                  f'  Nodes:{[i for i in routes_intersection if i != self.depot.ID]}\n')
        for current_route, route in enumerate(solution.routes):
            cost_per_route_verification.append(0)
            for current_position, node in enumerate(route):
                if current_position != 0:
                    node_a = route[current_position-1]
                    node_b = route[current_position]
                    cost_per_route_verification[current_route] += self.distance_matrix[node_a.ID][node_b.ID]
        total_cost_verification = sum(cost_per_route_verification)
        cost_diff = total_cost_verification - solution.total_cost
        if cost_diff > 1 or cost_diff < -1:
            print(f'  Cost calculation error. Difference: {cost_diff}'
                  f'  Done!')
        else:
            print(f'  No calculation error!\n'
                  f'  Done!')

    def vnd(self, construction_method=0, hard=True, detailed_print=True):
        # solve with vnd
        i_solution, o_solution = self.solve(hard=hard, construction_method=construction_method, length_of_rcl=1,
                                            optimisation_method=1)

        # check the solution for errors
        self.check_solution(o_solution)

        # print results
        if detailed_print:
            print(o_solution)
            print(f'  Initial solution cost: {round(i_solution.total_cost,4)}\n'
                  f'  Improvement: {round(o_solution.total_cost-i_solution.total_cost,4)}')
        else:
            print(f'  Optimised solution cost: {round(o_solution.total_cost, 4)}\n')

        return [i_solution, o_solution]

    def vnd_taboo(self, construction_method=0, hard=True, detailed_print=True):
        # solve with vnd
        i_solution, o_solution = self.solve(hard=hard, construction_method=construction_method, length_of_rcl=1,
                                            optimisation_method=2)

        # check the solution for errors
        self.check_solution(o_solution)

        # print results
        if detailed_print:
            print(o_solution)
            print(f'  Initial solution cost: {round(i_solution.total_cost,4)}\n'
                  f'  Improvement: {round(o_solution.total_cost-i_solution.total_cost,4)}')
        else:
            print(f'  Optimised solution cost: {round(o_solution.total_cost, 4)}\n')

        return [i_solution, o_solution]

    def vns(self, iterations=1000, limit=1000, hard=True, full_random_initial_solutions=False, detailed_print=True):
        best_cost = 10 ** 9
        best_solution = None
        initial_solution = None
        failed_to_improve = 0
        if full_random_initial_solutions:
            construction_method = 2
        else:
            construction_method = 0
        for _ in tqdm(range(iterations)):
            i_solution, o_solution = self.solve(hard=hard, construction_method=construction_method, length_of_rcl=3,
                                                optimisation_method=1)
            if o_solution.total_cost < best_cost:
                best_cost, best_solution, initial_solution = o_solution.total_cost, o_solution, i_solution
                failed_to_improve = 0
            else:
                failed_to_improve += 1
            if failed_to_improve == limit:
                break

        self.check_solution(best_solution)

        if detailed_print:
            print(best_solution)
            print(f'  Initial solution cost: {round(initial_solution.total_cost,4)}\n'
                  f'  Improvement: {round(best_solution.total_cost-initial_solution.total_cost,4)}')
        else:
            print(f'  Optimised solution cost: {round(best_solution.total_cost, 4)}\n')

        return [initial_solution, best_solution]
