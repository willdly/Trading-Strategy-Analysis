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

* In AWS console, Create a new Elastic Beanstalk Application
* Create a new environment for this application
   * Select Web Server Environment 
   * Select Python as the managed platform
   * For Application Code, select “upload your code”, and upload the .zip file containing the contents of the program
   * Create a new service role to be used (or select an existing one as applicable)
   * Create a new instance profile to be used (or select an existing one as applicable)
   * Skip Step 3 (networking, database, and tags)
   * In Step 4, select Load Balanced as the environment type, and increase the min/max number of instances as desired
* After creating the environment, navigate to IAM > Roles, and ensure that the service role and instance profile used in the above step have the following roles added to them: 
   * AdministratorAccess-AWSElasticBeanstalk
   * AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy	
   * AWSElasticBeanstalkMulticontainerDocker
   * AWSElasticBeanstalkWorkerTier
* Go to EC2 > Load Balancers, select the load balancer being used, then in the dropdown menu, select Edit Load Balancer Attributes. Here, modify the idle timeout to 4000. This allows the front end to stop from automatically timing out on longer optimization runs.

## Usage Instructions

![Program User Interface](https://github.com/callforhelp123/Trading-Strategy-Analysis/assets/34726256/35a138d6-3bae-450c-91e4-ffe743672fd4)

The program has three main functions: running optimizations, retrieving
results of past optimizations, and analyzing processed optimization run
results.

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

![Analyze Page](https://github.com/callforhelp123/Trading-Strategy-Analysis/assets/34726256/5928d6b3-483e-42a8-8d45-d20121c33815)


To analyze processed optimization run results, the user needs to start by selecting a
chart type. Depending on the chosen chart type, the dropdowns for "Select Ticker" 
and/or "Select Strategy" will be disabled. Click the "Go" button to generate
the selected chart based on the processed optimization run results. In addition, the 
user has the option to click on the "Update Processed Results" to get the latest 
optimization run results and updated dropdowns.

![Example Analyze Graph](https://github.com/callforhelp123/Trading-Strategy-Analysis/assets/34726256/eb0b7909-7a28-4073-806d-20cc781d6451)

When the chart of choice is processed, the user is displayed with an interactive and
informative plot provided by Plotly. For example, the Parameters vs Percent Return
plot, is presented with parameters used by the trading strategy and it's percent
return. From here, the user can understand how different parameter settings impact
the performance of their algorithm and assists decision-making for strategy improvements.
As for the other chart types, they all have the same purpose of helping remove emotional
interference from investment trading strategies and enhancing the user's trading decisions.
