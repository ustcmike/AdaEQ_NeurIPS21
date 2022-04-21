import gym
import numpy as np
import torch
import time
import sys
from redq.algos.redq_sac import REDQSACAgent
from redq.algos.core import mbpo_epoches, test_agent, get_redq_true_estimate_value
from redq.utils.run_utils import setup_logger_kwargs
from redq.utils.logx import EpochLogger
def redq_sac(env_name, seed=0, epochs='mbpo', steps_per_epoch=1000,
             max_ep_len=1000, n_evals_per_epoch=1,
             logger_kwargs=dict(), debug=False,
             # following are agent related hyperparameters
             hidden_sizes=(256, 256), replay_size=int(1e6), batch_size=256,
             lr=3e-4, gamma=0.99, polyak=0.995,
             alpha=0.2, auto_alpha=True, target_entropy='mbpo',
             start_steps=5000, delay_update_steps='auto',
             utd_ratio=20, num_Q=10, num_min=4, q_target_mode='min',
             policy_update_delay=20, threshold = 0.4
             ):
    """
    :param env_name: name of the gym environment
    :param seed: random seed
    :param epochs: number of epochs to run
    :param steps_per_epoch: number of timestep (datapoints) for each epoch
    :param max_ep_len: max timestep until an episode terminates
    :param n_evals_per_epoch: number of evaluation runs for each epoch
    :param logger_kwargs: arguments for logger
    :param debug: whether to run in debug mode
    :param hidden_sizes: hidden layer sizes
    :param replay_size: replay buffer size
    :param batch_size: mini-batch size
    :param lr: learning rate for all networks
    :param gamma: discount factor
    :param polyak: hyperparameter for polyak averaged target networks
    :param alpha: SAC entropy hyperparameter
    :param auto_alpha: whether to use adaptive SAC
    :param target_entropy: used for adaptive SAC
    :param start_steps: the number of random data collected in the beginning of training
    :param delay_update_steps: after how many data collected should we start updates
    :param utd_ratio: the update-to-data ratio
    :param num_Q: number of Q networks in the Q ensemble
    :param num_min: number of sampled Q values to take minimal from
    :param q_target_mode: 'min' for minimal, 'ave' for average, 'rem' for random ensemble mixture
    :param policy_update_delay: how many updates until we update policy network
    """
    #torch.autograd.set_detect_anomaly(True)
    if debug: # use --debug for very quick debugging
        hidden_sizes = [2,2]
        batch_size = 2
        utd_ratio = 2
        num_Q = 4
        max_ep_len = 100
        start_steps = 100
        steps_per_epoch = 100
    # use gpu if available
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # set number of epoch
    if epochs == 'mbpo' or epochs < 0:
        epochs = mbpo_epoches[env_name]
    total_steps = steps_per_epoch * epochs + 1
    """set up logger"""
    logger = EpochLogger(**logger_kwargs)
    logger.save_config(locals())
    """set up environment and seeding"""
    env_fn = lambda: gym.make(args.env)
    env, test_env = env_fn(), env_fn()
    # seed torch and numpy
    torch.manual_seed(seed)
    np.random.seed(seed)
    # seed environment along with env action space so that everything about env is seeded
    env.seed(seed)
    env.action_space.np_random.seed(seed)
    test_env.seed(seed + 10000)
    test_env.action_space.np_random.seed(seed + 10000)
    """prepare to init agent"""
    # get obs and action dimensions
    obs_dim = env.observation_space.shape[0]
    act_dim = env.action_space.shape[0]
    # if environment has a smaller max episode length, then use the environment's max episode length
    max_ep_len = env._max_episode_steps if max_ep_len > env._max_episode_steps else max_ep_len
    # Action limit for clamping: critically, assumes all dimensions share the same bound!
    # we need .item() to convert it from numpy float to python float
    act_limit = env.action_space.high[0].item()
    # keep track of run time
    start_time = time.time()
    # flush logger (optional)
    sys.stdout.flush()
    #################################################################################################
    """init agent and start training"""
    agent = REDQSACAgent(env_name, obs_dim, act_dim, act_limit, device, num_min, 
                 hidden_sizes, replay_size, batch_size,
                 lr, gamma, polyak,
                 alpha, auto_alpha, target_entropy,
                 start_steps, delay_update_steps,
                 utd_ratio, num_Q, q_target_mode,
                 policy_update_delay)
    o, r, d, ep_ret, ep_len = env.reset(), 0, False, 0, 0
    for t in range(total_steps):
        # get action from agent
        a = agent.get_exploration_action(o, env)
        # Step the env, get next observation, reward and done signal
        o2, r, d, _ = env.step(a)
        # give new data to agent
        agent.store_data(o, a, r, o2, d)
        # let agent update
        agent.train(logger)
        # set obs to next obs
        o = o2
        ep_ret += r
        ep_len += 1
        # Ignore the "done" signal if it comes from hitting the time
        # horizon (that is, when it's an artificial terminal signal
        # that isn't based on the agent's state)
        d = False if ep_len == max_ep_len else d
        if d or (ep_len == max_ep_len):
            # store episode return and length to logger
            logger.store(EpRet=ep_ret, EpLen=ep_len)
            # reset environment
            o, r, d, ep_ret, ep_len = env.reset(), 0, False, 0, 0

        # End of epoch wrap-up
        if (t+1) % steps_per_epoch == 0:
            epoch = t // steps_per_epoch
            # Test the performance of the deterministic version of the agent.
            test_agent(agent, test_env, max_ep_len, logger) # add logging here
            epoch_exp_error, epoch_std_error = get_redq_true_estimate_value(agent, logger, test_env, max_ep_len)

                   
            """logging"""
            # Log info about epoch
            logger.log_tabular('Epoch', epoch)
            logger.log_tabular('TotalEnvInteracts', t)
            logger.log_tabular('Time', time.time()-start_time)
            logger.log_tabular('EpRet', with_min_and_max=True)      
            logger.log_tabular('EpLen', average_only=True)         
            logger.log_tabular('TestEpRet', with_min_and_max=True) # Real Q value ?
            logger.log_tabular('TestEpLen', average_only=True)
            logger.log_tabular('Q1Vals', with_min_and_max=True)    # critic Q prediction ?
            logger.log_tabular('LossQ1', average_only=True)
            logger.log_tabular('LogPi', with_min_and_max=True)
            logger.log_tabular('LossPi', average_only=True)
            logger.log_tabular('Alpha', with_min_and_max=True)
            logger.log_tabular('LossAlpha', average_only=True)
            logger.log_tabular('PreTanh', with_min_and_max=True)
            logger.log_tabular('ExpError', average_only=True)
            logger.log_tabular('StdError', average_only=True)
            logger.log_tabular('M', agent.num_min)
            logger.dump_tabular()

            # flush logged information to disk
            sys.stdout.flush()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='Hopper-v2')
    parser.add_argument('--seed', '-s', type=int, default=0)
    parser.add_argument('--epochs', type=int, default=-1) # -1 means use mbpo epochs
    parser.add_argument('--exp_name', type=str, default='redq_sac')
    parser.add_argument('--data_dir', type=str, default='../old_data_real_adaptive/')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--threshold', '-t', type=float, default=0.4)
    parser.add_argument('--num_min', '-m', type=int, default=4)
    parser.add_argument('--q_target_mode', '-q', type=str, default='min')        

    args = parser.parse_args()

    # modify the code here if you want to use a different naming scheme
    exp_name_full = args.exp_name + '_%s' % args.env + 't_%s' % args.threshold + 'M_%s' % args.num_min + '_%s' % args.q_target_mode

    # specify experiment name, seed and data_dir.
    # for example, for seed 0, the progress.txt will be saved under data_dir/exp_name/exp_name_s0
    logger_kwargs = setup_logger_kwargs(exp_name_full, args.seed, args.data_dir)

    redq_sac(args.env, seed=args.seed, epochs=args.epochs,
             logger_kwargs=logger_kwargs, debug=args.debug, threshold = args.threshold, num_min=args.num_min, q_target_mode=args.q_target_mode)
