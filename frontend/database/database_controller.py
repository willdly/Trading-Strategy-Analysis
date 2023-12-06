from pymongo.mongo_client import MongoClient
from pymongo import DESCENDING
from datetime import datetime
from credentials import db_credentials
import pandas as pd


# Connect to MongoDB database and return the data stored within.
def get_database():
    uri = f"mongodb+srv://{db_credentials['username']}:{db_credentials['password']}@cluster0.mlx8ddf.mongodb.net/?retryWrites=true&w=majority"
    # Create a new client and connect to the server.
    client = MongoClient(uri)
    db = client[db_credentials["database"]]

    return db[db_credentials["collection"]]


# Retrieve prior optimization runs. The number of runs to retrieve is
# determined by num_limit argument.
def get_prior_runs(num_limit: int) -> dict:
    prior_runs = get_database().find().sort("_id", DESCENDING).limit(num_limit)
    return list(prior_runs)


# Retrieve prior optimization run corresponding to timestamp argument.
def get_run(timestamp):
    return get_database().find_one({"_id": timestamp})


# Add optimization results to database.
def add_results(document: dict, timestamp: datetime):
    document["_id"] = timestamp

    get_database().insert_one(document)


class ResultsProcessing:
    def __init__(self) -> None:
        # Create a new client and connect to the server.
        uri = f"mongodb+srv://{db_credentials['username']}:{db_credentials['password']}@cluster0.mlx8ddf.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri)
        self.db_connection = client[db_credentials["database"]]

        self.processed_db_connection = self.db_connection[
            db_credentials["collection2"]
        ]

        # If there is nothing in the processed_results collection the first time this code is ran
        try:
            self.processed_results = pd.DataFrame(
                self.processed_db_connection.find()
            )

            self.processed_results.drop(["_id"], axis=1, inplace=True)

        except KeyError:
            self.processed_results = None

        # dict of parameters for each strategy
        self._param_dict = {
            "Breakout": ["WL", "CSL", "DSL", "ATRP", "ATRM", "DB"],
            "Acceleration": ["SW", "LW"],
            "Velocity": ["SW", "LW", "RSI", "TSL"],
            "Exp/Con": ["SW", "LW", "CSL", "ATRM"],
        }
        # list of all parameters
        self._all_params = [
            "SW",
            "LW",
            "WL",
            "CSL",
            "DSL",
            "ATRP",
            "ATRM",
            "DB",
            "RSI",
            "TSL",
        ]

    def process_results(self):
        # create pandas dataframe of all results from Results collection (not processed)
        unprocessed_db = pd.DataFrame(get_database().find())

        # split dataframe by trading strategies
        breakout_df = self.parse_data(unprocessed_db, "Breakout")
        acceleration_df = self.parse_data(unprocessed_db, "Acceleration")
        expansion_df = self.parse_data(unprocessed_db, "Exp/Con")
        velocity_df = self.parse_data(unprocessed_db, "Velocity")

        # combine into one dataframe
        all_results_processed = pd.concat(
            [
                acceleration_df,
                breakout_df,
                expansion_df,
                velocity_df,
            ]
        )

        return all_results_processed

    def parse_data(self, data: pd.DataFrame, strategy: str):
        """
        Takes a DataFrame of the whole database of optimization results and returns an DataFrame of only
        the specified trading strategy results with its optimized parameters expanded to their own columns



        Parameters
        data: pd.DataFrame
            DataFrame columns ['_id', 'Exp/Con', 'inputs', 'Acceleration', 'Breakout', 'Velocity']
        strategy: str
            Should be either 'Exp/Con', 'Acceleration', 'Breakout' or 'Velocity'
        """

        # prep input dataframe
        cols_to_drop = [
            "_id",
            "Acceleration",
            "Breakout",
            "Exp/Con",
            "Velocity",
        ]
        cols_to_drop.remove(strategy)
        input_df = (
            data.drop(cols_to_drop, axis=1).dropna().reset_index(drop=True)
        )

        parsed_df = pd.DataFrame()

        # column names to rename to for analysis
        all_columns_names = [
            "ticker",
            "population_size",
            "generations",
            "cash",
            "commission",
            "start_date",
            "end_date",
            "inputs",
            "num_trades",
            "final_equity",
            "p_return",
            "p_max_drawdown",
            "p_avg_drawdown",
            "p_winrate",
            "sharpe_ratio",
            "p_exposure_time",
            "p_volatility",
            "p_buy_hold_return",
        ]

        # names from database dictionary
        input_row_column_order = [
            "ticker",
            "population_size",
            "generations",
            "cash",
            "commission",
            "start_date",
            "end_date",
        ]

        # names from database dictionary
        results_row_column_order = [
            "inputs",
            "# Trades",
            "Equity Final ($)",
            "Return (%)",
            "Max Drawdown (%)",
            "Avg Drawdown (%)",
            "Win Rate (%)",
            "Sharpe Ratio",
            "Exposure Time (%)",
            "Volatility (%)",
            "Buy & Hold Return (%)",
        ]

        # loop through all results and add each run to dataframe
        for idx in range(len(input_df.index) - 1):
            # the "inputs" for each row are the same, but may have many results
            new_input_row = (
                pd.DataFrame(input_df["inputs"][idx], index=[0])
                .reset_index(drop=True)
                .drop(["_id"], axis=1)
            )

            # rearrange columns to ensure they are they same order each time
            new_input_row = new_input_row[input_row_column_order]

            # loop through each backtesting result and add as a new row
            for key in input_df[strategy][idx]["results"].keys():
                results_row = pd.DataFrame.from_dict(
                    input_df[strategy][idx]["results"][key], orient="index"
                ).reset_index(drop=True)

                # rearrange columns to ensure they are they same order each time. needed!
                results_row = results_row[results_row_column_order]

                complete_new_row = pd.concat(
                    [new_input_row, results_row], ignore_index=True, axis=1
                )

                parsed_df = pd.concat(
                    [parsed_df, complete_new_row], ignore_index=True, axis=0
                )

        # rename column names
        parsed_df.columns = all_columns_names

        # # split inputs column into short window and long window columns
        parsed_df[self._param_dict[strategy]] = parsed_df["inputs"].str.split(
            "\n, ", expand=True
        )

        for p in self._param_dict[strategy]:
            parsed_df[p] = parsed_df[p].str.extract(r"(\d+\.\d+)")
            parsed_df[p] = parsed_df[p].astype("float64")

        # to datetime
        parsed_df["start_date"] = pd.to_datetime(
            parsed_df["start_date"], format="%Y-%m-%d"
        )
        parsed_df["end_date"] = pd.to_datetime(
            parsed_df["end_date"], format="%Y-%m-%d"
        )

        # add strategy_name
        parsed_df["strategy"] = strategy

        parsed_df.drop(
            ["inputs", "cash", "commission", "population_size", "generations"],
            axis=1,
            inplace=True,
        )

        return parsed_df

    def update_processed_results(self):
        # process all results from unprocessed database
        all_results_processed = self.process_results()

        # check if there is any data already processed
        if self.processed_results is None:
            self.processed_db_connection.insert_many(
                all_results_processed.to_dict("records")
            )

        # if this is the first time data is being added to processed_results collection
        else:
            # if there is data there. delete and re-add results.
            # pandas has issues matching duplicates with NaN values so only adding new results is difficult.
            # how the results are stored in the first place should be reconsidered
            self.processed_db_connection.delete_many(filter={})
            self.processed_db_connection.insert_many(
                all_results_processed.to_dict("records")
            )

        # update variable
        self.processed_results = pd.DataFrame(
            self.processed_db_connection.find()
        )
        self.processed_results.drop(["_id"], axis=1, inplace=True)

    def get_processed_results(self):
        return self.processed_results
