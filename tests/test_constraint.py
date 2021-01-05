import os
import random

import numpy as np
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset

from fairtorch import ConstraintLoss, DemographicParityLoss, EqualiedOddsLoss
import fairlearn
from sklearn import metrics as skm
from fairlearn import metrics as flm
from matplotlib import pyplot as plt 
from sklearn.decomposition import PCA
import pprint

def seed_everything(seed):
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True


seed_everything(2020)


def pytest_generate_tests(metafunc):
    # called once per each test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = sorted(funcarglist[0])
    metafunc.parametrize(
        argnames, [[funcargs[name] for name in argnames] for funcargs in funcarglist]
    )


class SensitiveDataset(Dataset):
    def __init__(self, x, y, sensitive):
        self.x = x.float()
        self.y = y.float()
        # self.y = np.ones(shape=y.shape).astype(np.float32)
        sensitive_categories = sensitive.unique().numpy()
        # print(sencat)
        self.category_to_index_dict = dict(
            zip(list(sensitive_categories), range(len(sensitive_categories)))
        )
        self.index_to_category_dict = dict(
            zip(range(len(sensitive_categories)), list(sensitive_categories))
        )
        self.sensitive = sensitive
        self.sensitive_ids = [
            self.category_to_index_dict[i] for i in self.sensitive.numpy().tolist()
        ]

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx].reshape(-1), self.sensitive_ids[idx]


class TestConstraint:
    params = {"test_costraint": [dict()]}

    def test_costraint(self):
        consloss = ConstraintLoss()
        assert isinstance(consloss, ConstraintLoss)


class TestDemographicParityLoss:
    params = {
        "test_dp": [dict(feature_dim=16, sample_size=128, dim_condition=2)],
        "test_eo": [dict(feature_dim=16, sample_size=128, dim_condition=2)],
        "test_train": [
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=None,
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=DemographicParityLoss(),
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=EqualiedOddsLoss(),
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
        ],
        "test_train_non_linear":[
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=None,
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=DemographicParityLoss(penalty="penalty"),
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=DemographicParityLoss(penalty="exact_penalty"),
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=DemographicParityLoss(penalty="barrier"),
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),

            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=EqualiedOddsLoss(),
                feature_dim=16,
                sample_size=16,
                dim_condition=2,
            ),
        ],
        "test_train_eval_nonlinear" :[
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=None,
                feature_dim=16,
                sample_size=2**10,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=DemographicParityLoss(penalty="penalty"),
                feature_dim=16,
                sample_size=2**10,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=DemographicParityLoss(penalty="exact_penalty"),
                feature_dim=16,
                sample_size=2**10,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=EqualiedOddsLoss(penalty="penalty", alpha=1),
                feature_dim=16,
                sample_size=2**10,
                dim_condition=2,
            ),
            dict(
                criterion=nn.BCEWithLogitsLoss(),
                constraints=EqualiedOddsLoss(penalty="exact_penalty", alpha=1),
                feature_dim=16,
                sample_size=2**10,
                dim_condition=2,
            ),

        ],
    }
    device = "cpu"

    def test_dp(self, feature_dim, sample_size, dim_condition):

        model = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, 1))
        dp_loss = DemographicParityLoss(sensitive_classes=[0, 1])
        assert isinstance(dp_loss, DemographicParityLoss)

        x_train = torch.randn((sample_size, feature_dim))
        sensitive_features = torch.randint(0, dim_condition, (sample_size,))
        out = model(x_train)

        mu = dp_loss.mu_f(x_train, out, sensitive_features)
        assert int(mu.size(0)) == dim_condition + 1

        loss = dp_loss(x_train, out, sensitive_features)
        assert float(loss) >= 0

    def test_eo(self, feature_dim, sample_size, dim_condition):
        model = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, 1))
        eo_loss = EqualiedOddsLoss(sensitive_classes=[0, 1])
        assert isinstance(eo_loss, EqualiedOddsLoss)
        x_train = torch.randn((sample_size, feature_dim))
        y = torch.randint(0, 2, (sample_size,))

        sensitive_features = torch.randint(0, dim_condition, (sample_size,))
        out = model(x_train)

        mu = eo_loss.mu_f(x_train, torch.sigmoid(out), sensitive_features, y=y)
        print(mu.size(), type(mu.size()))
        assert int(mu.size(0)) == (dim_condition + 1) * 2

        loss = eo_loss(x_train, out, sensitive_features, y)

        assert float(loss) >= 0

    def test_train(self, criterion, constraints, feature_dim, sample_size, dim_condition):
        torch.set_default_dtype(torch.float32)
        x = torch.randn((sample_size, feature_dim))
        y = torch.randint(0, 2, (sample_size,))
        sensitive_features = torch.randint(0, dim_condition, (sample_size,))
        dataset = SensitiveDataset(x, y, sensitive_features)
        train_size = len(dataset)
        train_dataset, test_dataset = torch.utils.data.random_split(
            dataset, [int(0.8 * train_size), train_size - int(0.8 * train_size)]
        )
        print(self.device)
        model = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, 1))
        model.to(self.device)
        optimizer = optim.Adam(model.parameters())
        train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
        model = self.__train_model(
            model=model,
            criterion=criterion,
            constraints=constraints,
            optimizer=optimizer,
            data_loader=train_loader,
        )


    def _generate_nolinear_data(self, sample_size, feature_dim, dim_condition):
        x = torch.randn((sample_size, feature_dim-1))
        sensitive_features = torch.randint(0, dim_condition, (sample_size,))
        print("x.shape, sensitive_features.shape",  x.shape, sensitive_features.shape)
        x = torch.cat([x, sensitive_features.reshape(sample_size, 1).float()], dim=1)
        gen_f = nn.Sequential(
                        nn.Linear(feature_dim, 16), nn.Tanh(),
                        nn.Linear(16, 8), nn.LeakyReLU(), 
                        nn.Linear(8, 1), nn.BatchNorm1d(1),
                        nn.Tanh()
                        )
        y_pred = gen_f.forward(x)
        y = y_pred > 0.0
        y = y.float()
        return x, y, sensitive_features


    def test_train_non_linear(self, criterion, constraints, feature_dim, sample_size, dim_condition):
        torch.set_default_dtype(torch.float32)
        x, y, sensitive_features = self._generate_nolinear_data(sample_size, feature_dim, dim_condition)
        dataset = SensitiveDataset(x, y, sensitive_features)
        train_size = len(dataset)
        train_dataset, test_dataset = torch.utils.data.random_split(
            dataset, [int(0.8 * train_size), train_size - int(0.8 * train_size)]
        )
        print(self.device)
        model = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
        model.to(self.device)
        optimizer = optim.Adam(model.parameters())
        train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
        model = self.__train_model(
            data_loader=train_loader,
            model=model,
            criterion=criterion,
            constraints=constraints,
            optimizer=optimizer)

    def test_train_eval_nonlinear(self, criterion, constraints, feature_dim, sample_size, dim_condition):
        torch.set_default_dtype(torch.float32)
        x, y, sensitive_features = self._generate_nolinear_data(sample_size, feature_dim, dim_condition)
        # plot_pca_x(x, y)
        # plt.hist(y.numpy())
        # plt.show()
        dataset = SensitiveDataset(x, y, sensitive_features)
        train_size = len(dataset)
        train_dataset, test_dataset = torch.utils.data.random_split(
            dataset, [int(0.8 * train_size), train_size - int(0.8 * train_size)]
        )
        print(self.device)
        model = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
        model.to(self.device)
        optimizer = optim.Adam(model.parameters())
        train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=256, shuffle=False)
        model = self.__train_model(
            data_loader=train_loader,
            model=model,
            criterion=criterion,
            constraints=constraints,
            optimizer=optimizer,
            max_epoch=10)
        result = self.__evaluate_model(model, criterion, test_loader)
        print("constraint: ", constraints)
        if constraints: 
            print("alpha: ", constraints.alpha)
        print(f'feature_dim: {feature_dim}, sample_size: {sample_size}')
        pprint.pprint(result)


    def __train_model(self, model, criterion, constraints, data_loader, optimizer, max_epoch=1):
        for epoch in range(max_epoch):
            for i, data in enumerate(data_loader):
                x, y, sensitive_features = data
                x = x.to(self.device)
                y = y.to(self.device)
                sensitive_features = sensitive_features.to(self.device)
                optimizer.zero_grad()
                # print(x.device, y.device, sensitive_features.device)
                # print(x.shape, y.shape, sensitive_features.shape)

                logit = model(x)
                assert isinstance(logit, torch.Tensor)
                assert isinstance(y, torch.Tensor)
                # print(x.device, y.device, sensitive_features.device, logit.device)

                loss = criterion(logit, y)
                if constraints:
                    penalty = constraints(x, logit, sensitive_features, y)
                    # print(penalty.requires_grad)
                    loss = loss + penalty
                loss.backward()
                optimizer.step()
        return model

    def __evaluate_model(self, model, criterion, data_loader):
        model.eval()
        y_true = []
        y_pred = []
        y_out = []
        sensitives = []
        for i, data in enumerate(data_loader):
            x, y, sensitive_features = data
            x = x.to(self.device)
            y = y.to(self.device)
            sensitive_features = sensitive_features.to(self.device)
            with torch.no_grad():
                logit = model(x)
            # logit : binary prediction size=(b, 1)
            bina = (torch.sigmoid(logit) > 0.5 ).float()
            y_true += y.cpu().tolist()
            y_pred += bina.cpu().tolist()
            y_out += torch.sigmoid(logit).tolist()
            sensitives += sensitive_features.cpu().tolist()
        result = {}
        result["acc"] = skm.accuracy_score(y_true, y_pred)
        result["f1score"] = skm.f1_score( y_true, y_pred)
        result["AUC"] = skm.roc_auc_score(y_true, y_out)
        result['DP'] = {
            "diff":flm.demographic_parity_difference(
                y_true,
                y_pred, 
                sensitive_features= sensitive_features),
            "ratio": flm.demographic_parity_ratio(
                y_true,
                y_pred, 
                sensitive_features= sensitive_features),
        }
        result["EO"] = {
            "diff":flm.equalized_odds_difference(
                y_true,
                y_pred, 
                sensitive_features= sensitive_features),
            "ratio": flm.equalized_odds_ratio(
                y_true,
                y_pred, 
                sensitive_features= sensitive_features),
        }
        return result


def plot_pca_x(x, y ,a =None):
    pca = PCA(n_components=2)
    x_2d = pca.fit_transform(x)
    assert x_2d.shape[0] == x.shape[0]
    assert x_2d.shape[1] == 2
    plt.scatter(x_2d[:, 0], x_2d[: , 1], c=y)
    plt.legend()
    plt.show()

