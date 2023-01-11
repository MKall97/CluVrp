from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None

np.random.seed(1)


class Clustering:

    def __init__(self, data):
        self.data = data
        self.nodes_clustered = None
        self.clusters = None
        self.n_clusters = None
        self.km = None

    def build_clusters(self, n_clusters):
        self.nodes_clustered = pd.DataFrame(self.data.nodes).transpose().apply(pd.to_numeric, errors='coerce')
        self.nodes_clustered.index = self.nodes_clustered.index.astype(int)
        self.nodes_clustered.head(5)
        self.n_clusters = n_clusters
        self.km = KMeans(n_clusters=n_clusters, n_init=10)
        depot = self.nodes_clustered.tail(1)
        depot['cluster'] = n_clusters
        self.nodes_clustered.drop(self.nodes_clustered.tail(1).index, inplace=True)
        y_predicted = self.km.fit_predict(self.nodes_clustered[['x', 'y']])
        self.nodes_clustered['cluster'] = y_predicted
        self.nodes_clustered = pd.concat([self.nodes_clustered, depot])
        self.clusters = pd.DataFrame(self.km.cluster_centers_, columns=['x', 'y'])

        # add depot cluster
        depot_row = pd.DataFrame([[0.0, 0.0]], columns=list('xy'), index=[n_clusters])
        self.clusters = pd.concat([self.clusters, depot_row])

        clu_dem = self.nodes_clustered.groupby(['cluster'])['demand'].sum()
        if sum(clu_dem > float(self.data.vehicle_profile['capacity'])) == 0:
            # print('Solvable!')
            return True
        else:
            # print('Not solvable :(\n', clu_dem > 550)
            return False

    def create_clusters(self, initial_number):
        # find feasible number of clusters and build them
        number_of_clusters = initial_number
        possible = False
        while not possible:
            # returns true or false depending on whether the problem is solvable for a given number of clusters
            # the problem is solvable when the vehicle's capacity can meet the demand of every cluster
            # (cluster_demand_i <= vehicle_capacity for every i in [0,number of clusters])
            possible = self.build_clusters(number_of_clusters)
            if possible:
                break
            number_of_clusters += 1
        return number_of_clusters
