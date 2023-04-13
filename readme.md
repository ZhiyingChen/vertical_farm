# Vertical Farm

**Introduction**

This is my master paper project. The dissertation file is Dissertation.pdf. The rest is the project.

**Environment Deployment**


Install Python Executor (version >= 3.7.0), Anaconda IDE is recommanded


The required packages are listed in requirements.txt. you can install them using:

    pip install -r requirements.txt

Install CPLEX (For this project, you need a CPLEX version >= 20.1.0.):

    1. run CPLEX installer.
    2. move to {CPLEX_HOME}/python, execute python setup.py.


**Run**

To run project:

    1. put your input data files in dataSet, or set your data path in solver.py
    2. execute python solver.py
	

**Notice**

The greedy algorithm mentioned in the dissertation is discarded as it cannot guarantee all demands to be met.




