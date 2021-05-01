# FairTorch
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-3-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

![FairTorchLogo](./fig/fairtorch_logo_vertical.png)

FairTorch won 1st prize at the [Global PyTorch Summer Hackathon 2020, Responsible AI section](https://pytorch.org/blog/announcing-the-winners-of-the-2020-global-pytorch-summer-hackathon/#pytorch-responsible-ai-development-tools).

PyTorch implementation of parity loss as constraints function to realize the fairness of machine learning.

Demographic parity loss and equalied odds loss are available.

This project is a part of [PyTorch Summer Hackathon 2020](https://pytorch2020.devpost.com/). visit our [project page](https://devpost.com/software/a-qeysp1).

## Usage

```python
dp_loss = DemographicParityLoss(sensitive_classes=[0, 1], alpha=100)
criterion = nn.BCEWithLogitsLoss()

.
.
.

logit = model(x_train)
loss = criterion(logit.view(-1), y_train)
loss = loss + dp_loss(x_train, logit, sensitive_features)
```

## Install

### pip version

```text
pip install fairtorch
```

### newest version

```text
git clone https://github.com/MasashiSode/fairtorch
cd fairtorch
pip install .
```

## Background

In recent years, machine learning-based algorithms and softwares have rapidly spread in society. However, cases have been found where these algorithms unintentionally suggest discriminatory decisions[1]. For example, allocation harms can occur when AI systems extend or withhold opportunities, resources, or information. Some of the key applications are in hiring, school admissions, and lending[2]. Since Pytorch didn't have a library to achieve fairness yet, we decided to create one.

## What it does

Fairtorch provides tools to mitigate inequities in classification and regression. Classification is only available in binary classification. A unique feature of this tool is that you can add a fairness constraint to your model by simply adding a few lines of code.

## Challenges we ran into

In the beginning, we attempted to develop FairTorch based on the [Fairlearn](https://github.com/fairlearn/fairlearn)[3]’s reduction algorithm. However, it was implemented based on scikit-learn and was not a suitable algorithm for deep learning. It requires ensemble training of the model, which would be too computationally expensive to be used for deep learning. To solve that problem, we implemented a constrained optimization without ensemble learning to fit the existing Fairlearn algorithm for deep learning.

## How we built it

We employ a method called group fairness, which is formulated by a constraint on the predictor's behavior called a parity constraint, where <img src="https://latex.codecogs.com/png.latex?X" title="X" /> is the feature vector used for prediction, <img src="https://latex.codecogs.com/png.latex?A" title="A" /> is a single sensitive feature (such as age or race), and <img src="https://latex.codecogs.com/png.latex?Y" title="Y" /> is the true label. A parity constraint is expressed in terms of an expected value about the distribution on <img src="https://latex.codecogs.com/png.latex?(X,&space;A,&space;Y)" title="(X, A, Y)" />.

In order to achieve the above, constrained optimization is adopted. We implemented loss as a constraint. The loss corresponds to parity constraints.

Demographic Parity and Equalized Odds are applied to the classification algorithm.

We consider a binary classification setting where the training
examples consist of triples <img src="https://latex.codecogs.com/png.latex?(X,&space;A,&space;Y)" title="(X, A, Y)" />, where X is a feature value, $A$ is a protected attribute, and <img src="https://latex.codecogs.com/png.latex?Y&space;\in&space;{0,&space;1}" title="Y \in {0, 1}" /> is a label.A classifier that predicts <img src="https://latex.codecogs.com/png.latex?X" title="Y" /> from <img src="https://latex.codecogs.com/png.latex?X" title="X" /> is <img src="https://latex.codecogs.com/png.latex?h:&space;X&space;\rightarrow&space;Y" title="h: X \rightarrow Y" />.

The demographic parity is shown below.

<img src="https://latex.codecogs.com/png.latex?E[h(X)|&space;A=a]&space;=&space;E[h(X)]&space;\&space;\rm{for&space;\&space;all}&space;\&space;a&space;\in&space;A" title="E[h(X)| A=a] = E[h(X)] \ \rm{for \ all} \ a \in A" />

Next, the equalized odds are shown below.

<img src="https://latex.codecogs.com/png.latex?E[h(X)|&space;A=a,&space;Y=y]&space;=&space;E[h(X)|Y=y]&space;\&space;\rm{for&space;\&space;all}&space;\&space;a\in&space;A,&space;\&space;y&space;\in&space;Y" title="E[h(X)| A=a, Y=y] = E[h(X)|Y=y] \ \rm{for \ all} \ a\in A, \ y \in Y" />

We consider learning a classifier <img src="https://latex.codecogs.com/png.latex?h(X;&space;\theta)" title="h(X; \theta)" /> by pytorch that satisfies these fairness conditions.
The <img src="https://latex.codecogs.com/png.latex?\theta" title="\theta" /> is a parameter. As an inequality-constrained optimization problem, we convert (1) and (2) to inequalities in order to train the classifier.

<img src="https://latex.codecogs.com/png.latex?M&space;\mu&space;(X,&space;Y,&space;A,&space;h(X,&space;\theta))&space;\leq&space;c" title="M \mu (X, Y, A, h(X, \theta)) \leq c" />

Thus, the study of the classifier <img src="https://latex.codecogs.com/png.latex?h(X;&space;\theta)" title="h(X; \theta)" /> is as follows.
<img src="https://latex.codecogs.com/png.latex?\rm{Min}_{\theta}" title="\rm{Min}_{\theta}" />s error <img src="https://latex.codecogs.com/png.latex?(X,&space;Y)" title="(X, Y)" /> subject to <img src="https://latex.codecogs.com/png.latex?M" title="M" /> <img src="https://latex.codecogs.com/png.latex?\mu&space;(X,&space;Y,&space;A,&space;h(X,&space;\theta))&space;\leq&space;c" title="\mu (X, Y, A, h(X, \theta)) \leq c" />
To apply this problem to pytorch's gradient method-based parameter optimization, we make the inequality constraint a constraint term R.

<img src="https://latex.codecogs.com/png.latex?R&space;=&space;B&space;\cdot&space;|ReLU(M&space;\mu&space;(X,&space;Y,&space;A,&space;h(X,&space;\theta))&space;-&space;c)|^2" title="R = B \cdot |ReLU(M \mu (X, Y, A, h(X, \theta)) - c)|^2" />

## Accomplishments that we're proud of

We confirmed by experiment that inequality is reduced just adding 2 lines of code.

## What We learned

What we learn is how to create criteria of fairness, the mathematical formulations to achieve it.

## What's next for FairTorch

As the current optimization algorithm is not yet refined in FairTorch, we plan to implement a more efficient constrained optimization algorithm. Other definitions of fairness have also been proposed besides demographic parity and equalized odds. In the future, we intend to implement other kinds of fairness.

## References

1. [the keynote by K. Crawford at NeurIPS 2017](https://youtu.be/fMym_BKWQzk)
2. [A Reductions Approach to Fair Classification (Alekh Agarwal et al.,2018)](http://proceedings.mlr.press/v80/agarwal18a.html)
3. Fairlearn: A toolkit for assessing and improving fairness in AI (Bird et al., 2020)

## Development

```text
poetry install
```

## Test

```text
pytest
```

## Authors

- [Akihiko Fukuchi](https://github.com/akiFQC)
- [Yoko Yabe](https://github.com/ykt345)
- [Masashi Sode](https://github.com/MasashiSode)

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://www.masashisode.com"><img src="https://avatars.githubusercontent.com/u/39261814?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Masashi Sode</b></sub></a><br /><a href="#infra-MasashiSode" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/wbawakate/fairtorch/commits?author=MasashiSode" title="Tests">⚠️</a> <a href="https://github.com/wbawakate/fairtorch/commits?author=MasashiSode" title="Code">💻</a> <a href="#maintenance-MasashiSode" title="Maintenance">🚧</a> <a href="#tutorial-MasashiSode" title="Tutorials">✅</a> <a href="https://github.com/wbawakate/fairtorch/pulls?q=is%3Apr+reviewed-by%3AMasashiSode" title="Reviewed Pull Requests">👀</a></td>
    <td align="center"><a href="https://github.com/akiFQC"><img src="https://avatars.githubusercontent.com/u/32811500?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Aki_FQC</b></sub></a><br /><a href="https://github.com/wbawakate/fairtorch/commits?author=akiFQC" title="Code">💻</a> <a href="https://github.com/wbawakate/fairtorch/commits?author=akiFQC" title="Tests">⚠️</a> <a href="#maintenance-akiFQC" title="Maintenance">🚧</a></td>
    <td align="center"><a href="https://github.com/ykt345"><img src="https://avatars.githubusercontent.com/u/3901603?v=4?s=100" width="100px;" alt=""/><br /><sub><b>yoko yabe</b></sub></a><br /><a href="#projectManagement-ykt345" title="Project Management">📆</a> <a href="#ideas-ykt345" title="Ideas, Planning, & Feedback">🤔</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
