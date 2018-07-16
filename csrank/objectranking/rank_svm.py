import logging

import numpy as np
import sklearn.preprocessing as prep
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.utils import check_random_state

from csrank.learner import Learner
from csrank.objectranking.object_ranker import ObjectRanker
from csrank.util import print_dictionary
from ..dataset_reader.objectranking.util import \
    generate_complete_pairwise_dataset

__all__ = ['RankSVM']


class RankSVM(ObjectRanker, Learner):
    _tunable = None

    def __init__(self, n_object_features, C=1.0, tol=1e-4, normalize=True,
                 fit_intercept=True, random_state=None, **kwargs):
        """ Create an instance of the RankSVM model.

        Parameters
        ----------
        n_object_features : int
            Number of features of the object space
        C : float, optional
            Penalty parameter of the error term
        tol : float, optional
            Optimization tolerance
        normalize : bool, optional
            If True, the data will be normalized before fitting.
        fit_intercept : bool, optional
            If True, the linear model will also fit an intercept.
        random_state : int, RandomState instance or None, optional
            Seed of the pseudorandom generator or a RandomState instance
        **kwargs
            Keyword arguments for the algorithms

        References
        ----------
        .. [1] Joachims, T. (2002, July).
               "Optimizing search engines using clickthrough data.",
               Proceedings of the eighth ACM SIGKDD international conference on
               Knowledge discovery and data mining (pp. 133-142). ACM.
        """
        self.normalize = normalize
        self.n_object_features = n_object_features
        self.C = C
        self.tol = tol
        self.logger = logging.getLogger('RankSVM')
        self.random_state = check_random_state(random_state)
        self.threshold_instances = int(1e10)
        self.fit_intercept = fit_intercept
        self.weights = None
        self.model = None

    def fit(self, X, Y, **kwargs):
        x_train, y_single = self.convert_instances(X, Y)
        if x_train.shape[0] > self.threshold_instances:
            self.model = LogisticRegression(C=self.C, tol=self.tol, fit_intercept=self.fit_intercept,
                                            random_state=self.random_state)
            self.logger.info("Logistic Regression model ")
        else:
            self.model = LinearSVC(C=self.C, tol=self.tol, fit_intercept=self.fit_intercept,
                                   random_state=self.random_state)
            self.logger.info("Linear SVC model ")

        if self.normalize:
            std_scalar = prep.StandardScaler()
            x_train = std_scalar.fit_transform(x_train)
        self.logger.debug('Finished Creating the model, now fitting started')

        self.model.fit(x_train, y_single)
        self.weights = self.model.coef_.flatten()
        if self.fit_intercept:
            self.weights = np.append(self.weights, self.model.intercept_)
        self.logger.debug('Fitting Complete')

    def convert_instances(self, X, Y):
        self.logger.debug('Creating the Dataset')
        x_train, garbage, garbage, garbage, y_single = generate_complete_pairwise_dataset(X, Y)
        del garbage
        assert x_train.shape[1] == self.n_object_features
        self.logger.debug('Finished the Dataset with instances {}'.format(x_train.shape[0]))
        return x_train, y_single

    def _predict_scores_fixed(self, X, **kwargs):
        assert X.shape[-1] == self.n_object_features
        self.logger.info("For Test instances {} objects {} features {}".format(*X.shape))
        if self.fit_intercept:
            scores = np.dot(X, self.weights[:-1])
        else:
            scores = np.dot(X, self.weights)
        self.logger.info("Done predicting scores")
        return np.array(scores)

    def predict_scores(self, X, **kwargs):
        return super().predict_scores(X, **kwargs)

    def predict_for_scores(self, scores, **kwargs):
        return ObjectRanker.predict_for_scores(self, scores, **kwargs)

    def predict(self, X, **kwargs):
        return super().predict(X, **kwargs)

    def clear_memory(self, **kwargs):
        pass

    def set_tunable_parameters(self, C=1.0, tol=1e-4, **point):
        self.tol = tol
        self.C = C
        if len(point) > 0:
            self.logger.warning('This ranking algorithm does not support'
                                ' tunable parameters'
                                ' called: {}'.format(print_dictionary(point)))
