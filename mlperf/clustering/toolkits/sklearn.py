"""SKLearn clustering"""

__author__ = "Vincenzo Musco (http://www.vmusco.com)"

from mlperf.clustering import clusteringtoolkit
from mlperf.clustering.clusteringtoolkit import ClusteringToolkit
from mlperf.tools.static import SKLEARN_TOOLKIT, SKLEARN__FAST_TOOLKIT, SKLEARN_TOL0_TOOLKIT
import random
import numpy as np
import sklearn.cluster


class Sklearn(clusteringtoolkit.ClusteringToolkit):
    """Toolkit class embedding utils functions"""

    def _clustering_to_list(self, data_without_target, model):
        clustering = []
        for index, row in data_without_target.iterrows():
            clustering.append([index, model[index]])
        return clustering

    def _centroids_to_list(self, model):
        centroids = []
        for row in model.cluster_centers_:
            centroids.append(row.tolist())
        return centroids

    def _init(self):
        if self.seed is not None:
            np.random.seed(self.seed)
            random.seed(self.seed)


class SklearnCustomTolerance(Sklearn):
    """Sklearn with custom tolerance"""

    def __init__(self, tolerance):
        super().__init__()
        self.tolerance = None

        self.set_tolerance(tolerance)

    def set_tolerance(self, value):
        self.tolerance = value
        if value is not None and type(value) == str:
            self.tolerance = float(value)

    def toolkit_name(self):
        return SKLEARN_TOL0_TOOLKIT

    def base_kmeans_specified_init(self, nb_clusters, src_file, data_without_target, dataset_name, run_number,
                                   init, run_info=None, nb_iterations=None):
        self._init()
        output_file, centroids_file = self._prepare_files(dataset_name, run_info, True)

        # Create a KMean model.
        params = {"n_clusters": nb_clusters, "init": init, "n_init": 1}
        if self.tolerance is not None:
            params['tol'] = self.tolerance
        if nb_iterations is not None:
            params['max_iter'] = nb_iterations

        sklearn_kmean_model = sklearn.cluster.KMeans(**params)
        sklearn_kmean_model.fit(data_without_target)

        ClusteringToolkit._save_clustering(self._clustering_to_list(data_without_target, sklearn_kmean_model.labels_),
                                           output_file)
        ClusteringToolkit._save_centroids(self._centroids_to_list(sklearn_kmean_model), centroids_file)

        return output_file, {"centroids": centroids_file}

    def run_kmeans_plus_plus(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None,
                             nb_iterations=None):
        return self.base_kmeans_specified_init(nb_clusters, src_file, data_without_target, dataset_name, run_number,
                                               'k-means++', run_info, nb_iterations)

    def run_kmeans_random(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None,
                          nb_iterations=None):
        return self.base_kmeans_specified_init(nb_clusters, src_file, data_without_target, dataset_name, run_number,
                                               'random', run_info, nb_iterations)

    def run_kmeans(self, nb_clusters, src_file, data_without_target, dataset_name, initial_clusters_file,
                   initial_clusters, run_number, run_info=None, nb_iterations=None):

        return self.base_kmeans_specified_init(nb_clusters, src_file, data_without_target, dataset_name, run_number,
                                               initial_clusters, run_info, nb_iterations)

    def run_gaussian(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None):
        self._init()
        output_file, = self._prepare_files(dataset_name, run_info, False)

        params = {'n_components': nb_clusters}
        if self.tolerance is not None:
            params['tol'] = self.tolerance

        built_model = sklearn.mixture.GaussianMixture(**params)
        built_model.fit(data_without_target)

        predicted_labels = built_model.predict(data_without_target)
        self._save_clustering(self._clustering_to_list(data_without_target, predicted_labels), output_file)

        return output_file, {}


class SklearnVanilla(SklearnCustomTolerance):
    """Sklearn with default tolerance"""

    def toolkit_name(self):
        return SKLEARN_TOOLKIT

    def __init__(self):
        super().__init__(None)

    def run_kmeans_plus_plus(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None,
                             nb_iterations=None):
        return super().run_kmeans_plus_plus(nb_clusters, src_file, data_without_target, dataset_name, run_number,
                                            nb_iterations)

    def run_kmeans(self, nb_clusters, src_file, data_without_target, dataset_name, initial_clusters_file,
                   initial_clusters, run_number, run_info=None, nb_iterations=None):
        return super().run_kmeans(nb_clusters, src_file, data_without_target, dataset_name, initial_clusters_file,
                                  initial_clusters, run_number, run_info, nb_iterations)

    def run_gaussian(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None):
        return super().run_gaussian(nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info)

    def run_hierarchical(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None):
        self._init()
        output_file, = self._prepare_files(dataset_name, run_info, False)

        built_model = sklearn.cluster.AgglomerativeClustering(n_clusters=nb_clusters)
        built_model.fit(data_without_target)

        self._save_clustering(self._clustering_to_list(data_without_target, built_model.labels_), output_file)

        return output_file, {}

    def run_meanshift(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None):
        self._init()
        output_file, centroids_file = self._prepare_files(dataset_name, run_info, True)

        # Create model.
        model = sklearn.cluster.MeanShift()
        model.fit(data_without_target)

        self._save_clustering(self._clustering_to_list(data_without_target, model.labels_), output_file)
        ClusteringToolkit._save_centroids(self._centroids_to_list(model), centroids_file)

        return output_file, {"centroids": centroids_file}

    def run_spectral(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None):
        self._init()
        output_file, = self._prepare_files(dataset_name, run_info, False)

        check = False

        while not check:
            try:
                built_model = sklearn.cluster.SpectralClustering(n_clusters=nb_clusters)
                built_model.fit(data_without_target)
                check = True
            except np.linalg.linalg.LinAlgError:
                continue
            except AssertionError:
                continue

            self._save_clustering(self._clustering_to_list(data_without_target, built_model.labels_), output_file)

        return output_file, {}

    def run_dbscan(self, nb_clusters, src_file, data_without_target, dataset_name, run_number, run_info=None):
        self._init()
        output_file, = self._prepare_files(dataset_name, run_info, False)

        eps_value = 0.33 * run_number
        sample_value = run_number % 10
        if sample_value == 0:
            sample_value = 10
        built_model = sklearn.cluster.DBSCAN(eps=eps_value, min_samples=sample_value)
        built_model.fit(data_without_target)

        self._save_clustering(self._clustering_to_list(data_without_target, built_model.labels_), output_file)

        return output_file, {}

    def run_ap(self, data_without_target, src_file, dataset_name, run_number, run_info=None):
        self._init()
        output_file, = self._prepare_files(dataset_name, run_info, False)

        damping_value = 0.016 * run_number + 0.5
        built_model = sklearn.cluster.AffinityPropagation(damping=damping_value)
        built_model.fit(data_without_target)

        self._save_clustering(self._clustering_to_list(data_without_target, built_model.labels_), output_file)

        return output_file, {}


class SklearnFast(Sklearn):
    def toolkit_name(self):
        return SKLEARN__FAST_TOOLKIT

    # TODO ?!
