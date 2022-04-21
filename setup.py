from os.path import join, dirname, realpath
from setuptools import setup
import sys

assert sys.version_info.major == 3 and sys.version_info.minor >= 6, \
    "Require Python 3.7 or greater."

setup(
    name='adaeq',
    py_modules=['adaeq'],
    version='0.0.3',
    install_requires=[
        'numpy',
        'joblib',
        'mujoco-py>=2.0.2.1',
        'gym>=0.17.2'
    ],
    description="Adaptive Ensemble Q-learning: Minimizing Estimation Bias via Error Feedback",
    author="Hang Wang, Sen Lin, Junshan Zhang",
)
