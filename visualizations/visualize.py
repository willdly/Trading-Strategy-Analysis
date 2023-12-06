from pymongo.mongo_client import MongoClient
from sklearn.ensemble import RandomForestRegressor
from pymongo import DESCENDING
from credentials import db_credentials
import pandas as pd
import plotly
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.offline as pyo
import math
import json
from database.database_controller import ResultsProcessing
from flask import Markup


class TSAVisualization:
    def __init__(self) -> None:
        # get processed results
        self.data = ResultsProcessing().get_processed_results()

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

    def plot_params_vs_return(self, ticker: str, strategy: str):
        """
        Plots the percent return vs parameter values for each parameter in the chosen strategy for the chosen ticker.
        Produces a different plot for each parameter

        Parameters
        ticker: str
            ETF name (e.g. TQQQ, TNA, FNGU, QQQ, etc.)
        strategy: str
            Should be either 'Exp/Con', 'Acceleration', 'Breakout' or 'Velocity'
        """

        if strategy == "Breakout":
            rows = 2
            columns = 3
        elif strategy == "Acceleration":
            rows = 1
            columns = 2
        elif strategy == "Exp/Con":
            rows = 2
            columns = 3
        else:
            rows = 2
            columns = 3

        fig = make_subplots(rows=rows, cols=columns)

        subplot_count = 1

        for index, param in enumerate(self._param_dict[strategy]):
            r = math.ceil(subplot_count / 3)
            c = index % 3 + 1

            trace_data = self.data[self.data["ticker"] == ticker]

            fig.add_trace(
                go.Scatter(
                    x=trace_data[param],
                    y=trace_data["p_return"],
                    mode="markers",
                    name=param,
                ),
                row=r,
                col=c,
            )
            fig["layout"][f"xaxis{index+1}"]["title"] = param

            subplot_count += 1

        fig.update_layout(
            title=f"{strategy} Parameters v.s. Percent Return <br> (ticker: {ticker})",
            title_x=0.5,
            yaxis_title="Percent Return",
            font=dict(
                family="Courier New, monospace", size=16, color="RebeccaPurple"
            ),
            height=rows * 500,
        )

        # return graph
        json_fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return json_fig

    def plot_drawdown_vs_return(self, ticker: str):
        plot_data = self.data[self.data["ticker"] == ticker]

        fig = px.scatter(
            plot_data,
            x="p_return",
            y="p_max_drawdown",
            color="strategy",
            hover_name="strategy",
            hover_data=self._all_params,
        )

        fig.update_layout(
            title=f"Price Breakout Parameters v.s. Percent Return <br> (ticker: {ticker})",
            title_x=0.5,
            yaxis_title="Max Percent Drawdown",
            xaxis_title="Percent Return",
            font=dict(
                family="Courier New, monospace", size=16, color="RebeccaPurple"
            ),
        )

        # return graph
        json_fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return json_fig

    def plot_feature_importance(self):
        fig = make_subplots(
            rows=2,
            cols=2,
            vertical_spacing=0.07,
            subplot_titles=["Exp/Con", "Acceleration", "Breakout", "Velocity"],
        )
        subplot_slots = [(1, 1), (1, 2), (2, 1), (2, 2)]

        for slot, strat in enumerate(
            ["Exp/Con", "Acceleration", "Breakout", "Velocity"]
        ):
            feature_names, values = self.get_feature_importance_data(
                strategy=strat
            )
            fig.add_trace(
                go.Bar(y=feature_names, x=values, name=strat, orientation="h"),
                row=subplot_slots[slot][0],
                col=subplot_slots[slot][1],
            )
            fig["layout"][f"xaxis{slot+1}"][
                "title"
            ] = "Gini Importance (Decreased Impurity)"
            fig["layout"][f"yaxis{slot+1}"]["title"] = "Features"

        fig.update_layout(
            title="Feature Importance for Trading Strategies",
            title_x=0.5,
            yaxis_title="Features",
            height=1250,
            width=1750,
            showlegend=False,
        )

        # return graph
        json_fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return json_fig

    def plot_trades_vs_return(self):
        tickers = list(self.data["ticker"].unique())
        strats = list(self.data.strategy.unique())

        fig = go.Figure()
        strategy_buttons = []

        for i, ticker in enumerate(tickers):
            tmp_df = self.data[self.data["ticker"] == ticker]

            fig.add_trace(
                go.Scatter(
                    x=tmp_df.num_trades,
                    y=tmp_df.p_return,
                    mode="markers",
                    name=ticker,
                )
            )

        for i, strat in enumerate(strats):
            visibility2 = ["legendonly"] * len(strats)
            visibility2[i] = True

            strategy_buttons.append(
                {
                    "label": strat,
                    "method": "update",
                    "args": [
                        {
                            "visible": visibility2,
                            "title": strat,
                            "showlegend": True,
                        }
                    ],
                }
            )

        strategy_buttons.insert(
            0,
            {
                "label": "All",
                "method": "update",
                "args": [
                    {
                        "visible": [True] * len(strats),
                        "title": "All",
                        "showlegend": True,
                    }
                ],
            },
        )

        fig.update_layout(
            {
                "updatemenus": [
                    {"type": "dropdown", "buttons": strategy_buttons}
                ]
            }
        )

        fig.update_layout(
            title="Number of Trades vs Percent Return",
            title_x=0.5,
            yaxis_title="Percent Return",
            xaxis_title="Number of Trades",
            font=dict(
                family="Courier New, monospace", size=16, color="RebeccaPurple"
            ),
        )

        # return graph
        json_fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return json_fig

    def get_feature_importance_data(self, strategy: str):
        # prep data for random forest
        data = self.data[self.data["strategy"] == strategy]
        data = pd.concat([data, pd.get_dummies(data["ticker"])], axis=1)
        x = data.drop(
            [
                "p_return",
                "p_winrate",
                "final_equity",
                "ticker",
                "strategy",
                "start_date",
                "end_date",
            ],
            axis=1,
        )
        x = x.dropna(axis=1)
        y = data["final_equity"]

        regressor = RandomForestRegressor(n_estimators=150, random_state=0)
        regressor.fit(x, y)

        return x.columns, regressor.feature_importances_
