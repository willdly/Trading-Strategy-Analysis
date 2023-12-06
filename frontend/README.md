# Cloud-based Optimization of Algorithmic Stock Market Trading Strategies


## Local Installation Instructions

* Create Python virtual environment and install dependencies.
    * Navigate to project directory in terminal
    * Create virtual environment:  python -m venv env
    * Activate virtual environment:  source env/bin/activate (POSIX) or
    env\Scripts\Activate.ps1 (PowerShell)
    * Install dependencies:  pip install -r requirements.txt
* Modify credentials.py with MongoDB server configuration.
    * Whitelist IP address in MongoDB and allow connections to applications
* Run program:  python application.py
* Use program on localhost in browser: http://localhost:8080


## Cloud Installation Instructions

We recommend deploying the program by using Elastic Beanstalk (EB) on Amazon
Web Services.

* Modify credentials.py with MongoDB server configuration.
    * Whitelist IP address in MongoDB and allow connections to applications
* Zip source code, including server configuration file found in
.platform/nginx/conf.d subdirectory.
* When configuring EB application, choose Load Balanced as the environment
type in the capacity section of Step 4: Configure instance traffic and scaling.
* After EB application and environment are launched, go to the application's
load balancer in the EC2 console and modify Idle timeout attribute to 4000.
* Use program by going to EB application domain in browser.


## Usage Instructions

![Program User Interface](https://i.ibb.co/c85t1kS/ui-screenshot.gif "Program User Interface")

The program has two main functions: running optimizations and retrieving
results of past optimizations.

In order to run a new optimization, user must provide a stock ticker, the
desired start date (01-01-2011 or later) and end date (06-01-2023 or before),
the number of populations and generations to run during the optimization
(must be between 1-1000 inclusive), and select which algorithms to optimize
for. Click on the Run Optimization button to start the optimization process.

![Example Results Graph](https://i.ibb.co/DVBsjpN/results-graph.gif "Example Results Graph")

When the optimization is done, a results graph for each selected algorithm
will display. The red dashed line represents the return for the standard
buy-and-hold strategy and serves as a baseline to compare the algorithm's
performance against. Hovering over a plot point will display the values of the
optimized parameters used during the backtest simulation as well as more
detailed results. An explanation of the parameter abbreviations is in the
graph's header.

The past optimizations dropdown menu stores the results of the last 10
optimization runs. Choose the desired run and click on the Get Optimization
button to display the results graphs for that run.
