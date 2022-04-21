# AdaEQ source code

This repo is the author's implementation of Adaptive Ensemble Q-learning (AdaEQ). The paper is available at https://openreview.net/pdf?id=YL6e9oSeInj. This code is a modification of the Randomized Ensembled Double Q-Learning (REDQ) algorithm. Paper link: https://arxiv.org/abs/2101.05982. 

# Update

We notice the REDQ algorithm has been updated lately in the author's repo (link: https://github.com/watchernyu/REDQ). Thanks to the effort by the author and we are also working hard on releasing the compatible version as soon as possible. 

## Code structure explained
The code structure is identical with REDQ algorithm. 

`experiments/train_ada.py`: Our implementation of AdaEQ algorithm.

`experiments/avg.py`: Our implementation of Averge-DQN algorithm.

`experiments/train_redq_sac.py`: you will find the main training loop. Here we set up the environment, initialize an instance of the `REDQSACAgent` class, specifying all the hyperparameters and train the agent. You can run this file to train a REDQ agent. 

`redq/algos/redq_sac.py`: We modify the original  `REDQSACAgent` to include the testing and error estimation function. 

`redq/algos/core.py`: We use the identical code as in REDQ algorithm which provides code for some basic classes (Q network, policy network, replay buffer) and some helper functions. These classes and functions are used by the REDQ agent class. 

`redq/utils`: We use the identical code as in REDQ algorithm which provides some utility classes (such as a logger) and helper functions that mostly have nothing to do with REDQ's core components. 

## Implementation tutorial
We plan to also release a video tutorial to help people understand and use the code. Once we finish it, we will post the link on this page. 

## Environment setup
Note: We use the idential setup as in REDQ. Please refer to https://github.com/watchernyu/REDQ for details.

## Train an REDQ agent
To train an AdaEQ agent, run:
```
python experiments/train_ada.py
```
To train an REDQ agent, run:
```
python experiments/train_redq_sac.py
```
To train an Averge-DQN agent, run:
```
python experiments/train_avg.py
```

## Acknowledgement

Our code for REDQ-SAC is partly based on the REDQ implementation (https://github.com/watchernyu/REDQ). 