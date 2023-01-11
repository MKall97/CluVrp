import random


class Tsp:
    def __init__(self, solver):
        self.distance_matrix = solver.distance_matrix
        self.cluster_routes = solver.cluster_routes
        self.clusters = solver.clusters
        self.depot = solver.depot
        self.hard = solver.hard
        self.length_of_rcl = solver.length_of_rcl
        self.construction_method = solver.construction_method
        self.solution = solver.solution

    def initialize_tsp(self):
        """Finds for each cluster route the nearest node to the depot."""
        for cluster_route in self.cluster_routes:
            min_dist = 10 ** 9
            for cluster in cluster_route.sequence_of_clusters:
                # Find nearest node to depot.
                if len(cluster.nodes) > 1:  # ignore depot cluster
                    for node in cluster.nodes:
                        candidate = self.distance_matrix[self.depot.ID][node.ID]
                        if candidate < min_dist:
                            min_dist = candidate
                            cluster_route.nearest_node = node

    def solve_randomly(self, nodes, current_route):
        # random solution
        not_routed = nodes.copy()
        while not_routed:
            inserted_customer = random.choice(not_routed)
            not_routed = [i for i in not_routed if i.ID != inserted_customer.ID]
            current_route.add(inserted_customer, self.distance_matrix)

    def find_neighbors(self, node, nodes_list):
        """
        Finds a number of the nearest neighbors of a node in a nodes-list.
        Input a length (self.length_of_rcl) bigger than 1 to activate the restricted candidate list mode.
        This mode helps to generate diverse initial solutions to explore a wider part of
        the solution space during the local search
        """
        for candidate in nodes_list:
            if node == candidate:
                continue
            if candidate.is_routed:
                continue
            cost = self.distance_matrix[node.ID][candidate.ID]
            if len(node.neighbors) < self.length_of_rcl:
                new_tup = (cost, candidate)
                node.neighbors.append(new_tup)
                node.neighbors.sort(key=lambda x: x[0])
            elif cost < node.neighbors[-1][0]:
                node.neighbors.pop(len(node.neighbors) - 1)
                new_tup = (cost, candidate)
                node.neighbors.append(new_tup)
                node.neighbors.sort(key=lambda x: x[0])

    def apply_nearest_neighbor(self, nodes, current_route):
        # nearest neighbor solution
        all_routed = all([node.is_routed for node in nodes])
        while not all_routed:
            last_routed_customer = current_route.sequence_of_nodes[-2]
            # the construction_method below  returns the list of candidate customers and finds the neighbors of
            # last_routed_customer in that list
            self.find_neighbors(last_routed_customer, nodes)
            inserted_customer = random.choice(last_routed_customer.neighbors)
            current_route.add(inserted_customer[1], self.distance_matrix)
            all_routed = all([node.is_routed for node in nodes])

    def find_minimum_insertion(self, nodes, current_route):
        candidate = None
        insertion_position = None
        # only for minimum insertion algorithm:
        # add the cost of traveling from first inserted node to the depot, because it will be removed later
        if len(current_route.sequence_of_nodes) == 3:  # [Depot, Node, Depot]
            first_inserted_node = current_route.sequence_of_nodes[-2]
            current_route.cost += self.distance_matrix[first_inserted_node.ID][self.depot.ID]
        for customer in nodes:
            min_cost = 10 ** 9
            if not customer.is_routed and customer.ID != self.depot.ID:
                for current_position, routed in enumerate(current_route.sequence_of_nodes):
                    if current_position != 0:
                        insertion = current_route.sequence_of_nodes[current_position - 1], customer, \
                            current_route.sequence_of_nodes[current_position]
                        # old edge -> [node_a,node_b] (remove this cost)
                        node_a = insertion[0]
                        node_b = insertion[2]

                        # new edges -> [node_a, node_x: candidate, node_b] (add these two new costs)
                        node_x = insertion[1]

                        # new cost = cost(node_a->node_x) + cost(node_x->node_b) - cost(node_a->node_b)
                        cost = self.distance_matrix[node_a.ID][node_x.ID] + \
                               self.distance_matrix[node_x.ID][node_b.ID] - \
                               self.distance_matrix[node_a.ID][node_b.ID]

                        if cost < min_cost:
                            min_cost = cost
                            candidate = customer
                            insertion_position = current_position

                current_route.sequence_of_nodes.insert(insertion_position, candidate)
                current_route.cost += min_cost
                current_route.load += candidate.demand
                candidate.is_routed = True

    def apply_minimum_insertions(self, nodes, current_route):
        all_routed = all([node.is_routed for node in nodes])
        while not all_routed:
            self.find_minimum_insertion(nodes, current_route)
            all_routed = all([node.is_routed for node in nodes])

    def apply_construction_method(self, node_list, current_route):
        """
        Applies one of three construction methods depending on the user's choice
        :param node_list: The nodes meant for routing
        :param current_route:  Route under construction
        """
        if self.construction_method == 2:
            self.solve_randomly(node_list, current_route)
        elif self.construction_method == 0:
            self.apply_nearest_neighbor(node_list, current_route)
        elif self.construction_method == 1:
            self.apply_minimum_insertions(node_list, current_route)

    def construct_solution(self):
        """
        Constructs initial solution for hard clustered or soft clustered problems
        """

        # initialize the solution by finding the nearest nodes to the depot from each cluster_route
        self.initialize_tsp()

        # construct an initial solution for each cluster route:
        last_customer = None
        for cluster_route in self.cluster_routes:

            # define current route
            current_route = cluster_route.node_route

            # add depot, and then the nearest node first via the custom "add" construction_method of our Route object
            current_route.sequence_of_nodes.append(self.depot)

            current_route.sequence_of_nodes.append(cluster_route.nearest_node)
            current_route.cost += self.distance_matrix[cluster_route.nearest_node.ID][self.depot.ID]
            current_route.load += cluster_route.nearest_node.demand
            cluster_route.nearest_node.is_routed = True

            current_route.sequence_of_nodes.append(self.depot)

            # find the number of customers for each cluster route (for later use)
            cluster_route.number_of_customers = \
                sum([len(cluster.nodes) for cluster in cluster_route.sequence_of_clusters]) - 2

            # the problem will be tackled differently if we define it as hard clustered or soft clustered
            if self.hard:

                # if hard, solve each cluster distinctly
                # first, serve the cluster of the nearest node
                if len(current_route.sequence_of_nodes) == 3:  # [Depot, Nearest Node, Depot]
                    for cluster in cluster_route.sequence_of_clusters:
                        if cluster.ID == cluster_route.nearest_node.cluster:
                            first = cluster
                            self.apply_construction_method(first.nodes, current_route)
                    if self.construction_method != 1:  # in case of using the nearest neighbor or random
                        # algorithm, we need to manually add the cost of traveling from the last customer to the depot
                        last_customer = current_route.sequence_of_nodes[-2]
                        current_route.cost += self.distance_matrix[last_customer.ID][self.depot.ID]

                # Serve the rest of clusters if they exist in the cluster route
                if len(cluster_route.sequence_of_clusters) > 3:
                    if self.construction_method != 1:
                        current_route.cost -= self.distance_matrix[last_customer.ID][self.depot.ID]
                    for cluster in cluster_route.sequence_of_clusters:
                        # the cluster of the nearest node has already been serviced, so we must skip it
                        # we also skip the depot cluster
                        if cluster.ID == cluster_route.nearest_node.cluster or cluster.ID == self.depot.cluster:
                            continue
                        self.apply_construction_method(cluster.nodes, current_route)
                    if self.construction_method != 1:
                        last_customer = current_route.sequence_of_nodes[-2]
                        current_route.cost += self.distance_matrix[last_customer.ID][self.depot.ID]

            else:
                # in case we tackle the problem as soft clustered, the whole cluster-route will be solved as
                # a tsp instance
                node_list = []
                for cluster in cluster_route.sequence_of_clusters:
                    # create a node list by merging the nodes of each cluster while ignoring the depot
                    if cluster.ID == self.depot.cluster:
                        continue
                    node_list += cluster.nodes
                    # solve the tsp instance
                    self.apply_construction_method(node_list, current_route)
                if self.construction_method != 1:
                    last_customer = current_route.sequence_of_nodes[-2]
                    current_route.cost += self.distance_matrix[last_customer.ID][self.depot.ID]

            self.solution.routes.append(cluster_route.node_route.sequence_of_nodes)
            self.solution.cost_per_route.append(cluster_route.node_route.cost)
            self.solution.total_cost += cluster_route.node_route.cost
