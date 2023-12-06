from flask import Flask, render_template, request, make_response, jsonify
import database.database_controller as db
import requests
from datetime import datetime
from visualizations.visualize import TSAVisualization

application = Flask(__name__)
tsva = TSAVisualization()


# dash_app.plot_drawdown_vs_return(application)
# dash_app.plot_params_vs_return(application)


@application.route("/")
def index():
    url = "http://18.222.8.195:5000/algo_list"
    response = requests.get(url)
    if response.status_code == 200:
        algorithm_labels = response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return render_template("index.html", labels=algorithm_labels)


@application.route("/optimize", methods=["GET"])
def get_prior_runs():
    return db.get_prior_runs(10)


@application.route("/optimize/<timestamp>", methods=["GET"])
def get_timestamp_results(timestamp):
    return db.get_run(timestamp)


@application.route("/optimize", methods=["POST"])
def run_optimization():
    parameters = request.get_json()
    accept_types: list[str] = request.accept_mimetypes

    if (
            "ticker" in parameters
            and "populationSize" in parameters
            and "generations" in parameters
            and "endDate" in parameters
            and "startDate" in parameters
    ):
        ticker = parameters["ticker"]
        population_size = parameters["populationSize"]
        generations = parameters["generations"]
        start_date = parameters["startDate"]
        end_date = parameters["endDate"]
        selected_algos = parameters["selectedAlgos"]

        url = "http://18.222.8.195:5000/optimize" # got it working on a microservice :')
        data = {
            "ticker": ticker,
            "population_size": population_size,
            "generations": generations,
            "start_date": start_date,
            "end_date": end_date,
            "selected_algos": selected_algos
        }

        response = requests.post(url, json=data)
        optimized_results = response.json()
        date_format = '%a, %d %b %Y %H:%M:%S GMT'

        optimized_results['inputs']['_id'] = datetime.strptime(optimized_results['inputs']['_id'], date_format)
        if optimized_results and len(optimized_results) > 0:
            db.add_results(optimized_results,
                           optimized_results['inputs']['_id'])

            if "text/html" in accept_types:
                html_results = render_template(
                    "backtest.jinja", data=optimized_results
                )
                response = make_response(html_results)
                response.headers.set("Content-Type", "text/html")
                response.status_code = 201
                return response

            elif "application/json" in accept_types:
                response = jsonify(optimized_results)
                response.headers.set("Content-Type", "application/json")
                response.status_code = 201
                return response

            else:
                return 406

        else:
            return 400

    else:
        return 400


@application.route('/analyze')
def analyze():
    # Get unique ticker values from tsva.data
    unique_tickers = list(tsva.data['ticker'].unique())

    return render_template("visualize.html", unique_tickers=unique_tickers)


@application.route("/graph", methods=["GET"])
def render_analyze():
    graphJSON = None  # Initialize graphJSON

    # example request
    # http://127.0.0.1:8080/visualize?type=ParamReturn&ticker=TQQQ&strategy=Breakout
    plot_type = request.args.get("type", None)
    ticker = request.args.get("ticker", None)
    strategy = request.args.get("strategy", None)

    if plot_type == "ParamReturn":
        graphJSON = tsva.plot_params_vs_return(
            ticker=ticker, strategy=strategy
        )

    elif plot_type == "DrawdownReturn":
        graphJSON = tsva.plot_drawdown_vs_return(ticker=ticker)

    elif plot_type == "Features":
        graphJSON = tsva.plot_feature_importance()

    elif plot_type == "TradesReturn":
        graphJSON = tsva.plot_trades_vs_return()

    return graphJSON


@application.route('/update_results', methods=['POST'])
def update_results():
    try:
        # Import necessary function from database_controller.py
        from database.database_controller import ResultsProcessing

        # Create an instance of ResultsProcessing and call the update_processed_results method
        results_processor = ResultsProcessing()
        results_processor.update_processed_results()

        # Get the updated unique tickers
        unique_tickers = list(tsva.data['ticker'].unique())

        # Return a response with the updated tickers
        return {'status': 'success', 'message': 'Processed results updated successfully', 'tickers': unique_tickers}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}


if __name__ == "__main__":
    application.run(host="127.0.0.1", port=8080, debug=True)
