'use strict';

var storedOptimizations = [];

window.addEventListener('load', function() {
  console.log("Hello Trading World!");
  storedOptimizations = loadOptimizationList();
});

// Submit user inputs to optimizer and display the optimization results.
const runOptimization = async() => {
  // Validate user inputs.
  const inputBody = validateInputs();
  if (inputBody == "") {
    return;
  }

  // Reset results display.
  document.getElementById("response-results").innerHTML = "";
  document.getElementById("response-inputs").innerHTML = "";

  // Start processing timer.
  let seconds = 0;
  let timerId = setInterval(function() {
    document.getElementById("response-results").innerHTML = "Processing Time: " + ++seconds + " seconds";
  }, 1000);

  // Disable user input/submit button while optimization is running.
  disableInputs();

  // Send user inputs to optimizer.
  console.log("Data sent!");
  let acceptType = 'application/json';
  const response = await fetch('/optimize', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Accept': acceptType
    },
    body: inputBody
  });

  // Display results of optimization and update list of past optimizations.
  const resultsDiv = document.getElementById('response-results');
  if (response.status == 201 && response.headers.get('content-type') == 'text/html') {
    const htmlResponse = await response.text();
    resultsDiv.innerHTML = htmlResponse;
  }

  else if (response.status == 201 && response.headers.get('content-type') == 'application/json') {
    const jsonResponse = await response.json();
    console.log(jsonResponse);
    storedOptimizations.unshift(jsonResponse);
    populateDropdown();
    createPlot(resultsDiv, jsonResponse);
  }

  else {
    resultsDiv.innerHTML = '';
    alert("Error occurred during optimization. No results to report.");
    console.log("Error occurred during optimization. No results to report.");
  }

  // Clear timer and re-enable user inputs/submit button.
  clearInterval(timerId);
  enableInputs();
}

// Display results of a prior optimization.
const loadOptimization = async() => {
  var dropdown = document.getElementById('optimization-list');
  var selectedValue = dropdown.value;
  console.log(selectedValue);

  if (selectedValue == "") {
    alert("No selection made!");
    return;
  }

  // Iterate through past optimizations to find requested run. 
  for (var i = 0; i < storedOptimizations.length; i++) {
    if (storedOptimizations[i]._id == selectedValue) {
      const resultsDiv = document.getElementById('response-results');
      createPlot(resultsDiv, storedOptimizations[i]);
      return;
    }
  }
}

// Create dropdown list of past optimization runs.
const loadOptimizationList = async() => {
  let acceptType = 'application/json';
  const response = await fetch('/optimize', {
      method: 'GET',
      headers: {
        'Accept': acceptType
      },
  });

  storedOptimizations = await response.json();
  populateDropdown();
}

// Populate dropdown list with past optimization runs.
const populateDropdown = async() => {
  var dropdown = document.getElementById("optimization-list");
  dropdown.innerHTML = "";

  console.log("Loading past optimizations...");
  console.log(storedOptimizations);
  for (var i = 0; i < storedOptimizations.length; i++) {
      var option = document.createElement('option');
      var inputs = storedOptimizations[i].inputs;
      option.text = `${inputs.ticker}; ${inputs.start_date} --> ${inputs.end_date}; Pop/Gen: ${inputs.population_size}/${inputs.generations}`;
      option.value = storedOptimizations[i]._id;
      dropdown.add(option);
  }
}

// Create a plot graph to display results of optimization.
function createPlot(resultsDiv, algoDict) {
  resultsDiv.innerHTML = '';

  // Iterate through algoDict to create each algorithm's plot graph.
  for (let [algo, algoData] of Object.entries(algoDict)) {
    if (algo == '_id') {
      continue;
    }

    // Display the results header.
    if (algo == 'inputs') {
      let responseInputs = document.getElementById("response-inputs");
      responseInputs.innerHTML = `${algoData.ticker}<br>${algoData.start_date} to ${algoData.end_date}<br>Pop/Gen Size: ${algoData.population_size}/${algoData.generations}`;
      continue;
    }

    let description = algoData['description'];
    let data = Object.values(algoData['results']).map(d => Object.values(d)[0]);
    console.log(data);

    // Create plot points.
    var trace = {
      x: data.map(d => d['Return (%)']),
      y: data.map(d => d['Max Drawdown (%)']),
      mode: 'markers',
      type: 'scatter',
      text: data.map(d => {
        let result = '';
        for (let key in d) {
              if (key == "inputs"){
                result += `${d[key]}<br>`;
              } else {
            result += `${key}: ${d[key]}<br>`;
            }
          }
        return result;
      }),
      hoverinfo: 'text',
    };

    // let allReturns = data.map(d => d['Return (%)']);
    // let minX = Math.min(...allReturns) - 10;
    // let maxX = Math.max(...allReturns) + 10;
    let allDrawdowns = data.map(d => d['Max Drawdown (%)']);
    let minY = Math.min(...allDrawdowns) - 10;
    let maxY = Math.max(...allDrawdowns) + 10;
    let buyandhold = data[0]['Buy & Hold Return (%)'];

    var layout = {
        xaxis: {
            title: 'Return (%)',
            autorange: true
        },
        yaxis: {
            title: 'Max Drawdown (%)',
            autorange: true
        },
        title: algo,
        margin: {
          t: 120 // Increase the top margin value to create space for the annotation
        },
        annotations: [
          {
              xref: 'paper',
              yref: 'paper',
              x: 0.5,
              y: 1.20,
              xanchor: 'center',
              yanchor: 'top',
              text: replace_new_lines(description),
              showarrow: false,
              font: {
                  size: 12
              },
              align: 'center',
              valign: 'top',
              borderpad: 0,
              height: 120
          },
          {
            xref: 'x',
            yref: 'y',
            x: buyandhold,
            y: (maxY + minY) / 2, // Adjust the vertical positioning as desired
            xanchor: 'right',
            yanchor: 'middle',
            text: 'Buy and Hold',
            showarrow: false,
            font: {
                size: 12
            },
            textangle: -90, // Rotate the text vertically
            standoff: 10, // Adjust the distance between the text and the line
        }
      ],
      shapes: [
        {
          type: 'line',
          x0: buyandhold,
          y0: maxY,
          x1: buyandhold,
          y1: minY,
          line: {
            color: 'red',
            width: 2,
            dash: 'dot',
          }
        }
      ]
    };

    // Create a div for each plot point.
    let newDiv = document.createElement('div');
    newDiv.id = algo;  // Give each div a unique id
    resultsDiv.appendChild(newDiv);

    // Center the graph and set max width.
    newDiv.style.display = "block";
    newDiv.style.margin = "auto";
    newDiv.style.maxWidth = "800px";

    // Create graph.
    Plotly.newPlot(algo, [trace], layout);

    // Create a new div.
    let newDiv2 = document.createElement('div');

    // Add inline styles to the div.
    newDiv2.style.marginTop = '20px';

    // Append the new div to the parent div.
    resultsDiv.appendChild(newDiv2);
  }
}

function replace_new_lines(text){
  var converted_text = text.replace(/\n/g, "<br>");
  return converted_text;
}

/*
Validates user inputs including stock ticker. 
If any user input is invalid, user is notified via alert and nothing is
returned. If all inputs are valid, user inputs are returned in a JSON
dictionary.
*/
function validateInputs() {
  let populationSize = document.getElementById("populationsize").value;
  let generations = document.getElementById("generations").value;
  let ticker = document.getElementById("ticker").value;
  let startDate = document.getElementById("startdate").value;
  let endDate = document.getElementById("enddate").value;

  if (!validateInput(populationSize, 1, 1000, "Invalid population size!")) {
    return "";
  }

  if (!validateInput(generations, 1, 1000, "Invalid generation size!")) {
    return "";
  }

  if (!validateStockTicker(ticker)) {
    return "";
  }

  if (!validateStartDate(startDate, endDate)) {
    return "";
  }

  if (!validateEndDate(endDate)) {
    return "";
  }

  var checkboxValues = [];

  var checkboxes = document.querySelectorAll('input[type="checkbox"]');
  checkboxes.forEach(function(checkbox) {
    checkboxValues.push(checkbox.checked);
  });

  return JSON.stringify({ 
    populationSize: parseInt(populationSize),
    generations: parseInt(generations),
    ticker: ticker,
    startDate: startDate,
    endDate: endDate,
    selectedAlgos: checkboxValues
  });
}

// Helper function for validateInputs to validate submitted population and
// generation sizes.
function validateInput(value, rangeMin, rangeMax, errorMessage) {
  if (isNaN(value) || value < rangeMin || value > rangeMax) {
    alert(`${errorMessage} Range [${rangeMin}, ${rangeMax}]`);
    return false;
  }
  return true;
}

// Helper function for validateInputs to validate submitted stock ticker.
function validateStockTicker(ticker) {
  // Ticker can not be empty or contain any invalid characters.
  if (!ticker || !/^[A-Za-z0-9]+$/.test(ticker)) {
    alert("Invalid stock ticker!");
    return false;
  }
  return true;
}

// Helper function for validateInputs to validate submitted start date.
function validateStartDate(startDate, endDate) {
  // Convert date strings to Date objects.
  const startDateObj = new Date(startDate);
  const endDateObj = new Date(endDate);

  // Start date can not be empty and must be both after 01-01-2010 and before
  // the submitted end date.
  if (isNaN(startDateObj) || startDateObj < new Date("2010-01-01") || startDateObj > endDateObj) {
    alert("Invalid start date! Must be 01-01-2010 or later and before end date.");
    return false;
  }
  return true;
}

// Helper function for validateInputs to validate submitted end date.
function validateEndDate(endDate, startDate) {
  // Convert date string to Date object.
  const endDateObj = new Date(endDate);

  // End date can not be empty and must be before 06-01-2023.
  if (isNaN(endDateObj) || endDateObj > new Date("2023-06-01")) {
    alert("Invalid end date! Must be 06-01-2023 or earlier.");
    return false;
  }
  return true;
}

// Disable user inputs and "run" button.
function disableInputs() {
  let inputHeaders = document.getElementsByClassName("inputheader");
  for (let i = 0; i < inputHeaders.length; i++) {
    let inputs = inputHeaders[i].getElementsByTagName("input");
    for (let j = 0; j < inputs.length; j++) {
      inputs[j].disabled = true;
    }
  }

  var buttons = document.getElementsByClassName("run");
  for(var i = 0; i < buttons.length; i++) {
    buttons[i].disabled = true;
  }
}

// Enable user inputs and "run" button.
function enableInputs() {
  let inputHeaders = document.getElementsByClassName("inputheader");
  for (let i = 0; i < inputHeaders.length; i++) {
    let inputs = inputHeaders[i].getElementsByTagName("input");
    for (let j = 0; j < inputs.length; j++) {
        inputs[j].disabled = false;
    }
  }

  var buttons = document.getElementsByClassName("run");
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].disabled = false;
  }
}

/**
 * Handles the change in plot type.
 *
 * @param {none} - This function does not take any parameters.
 * @return {none} - This function does not return anything.
 */
function handlePlotTypeChange() {
    var plotTypeSelect = document.getElementById('type');
    var tickerSelect = document.getElementById('ticker');
    var strategySelect = document.getElementById('strategy');

    strategySelect.disabled = (plotTypeSelect.value === 'DrawdownReturn' || plotTypeSelect.value === 'Features' || plotTypeSelect.value === 'TradesReturn');
    tickerSelect.disabled = (plotTypeSelect.value === 'Features' || plotTypeSelect.value === 'TradesReturn');
}

/**
 * Handles the form submit event for the analyze form.
 *
 * @param {FormData} form - The form data object containing the form fields.
 * @return {void} This function does not return anything.
 */
function handleAnalyzeFormSubmit(form) {
    var formData = new FormData(form);

    fetch(form.action + '?' + new URLSearchParams(formData).toString(), {
        method: 'GET'
    })
    .then(response => response.json())
    .then(graphJSON => {
        console.log('Received Graph Data:', graphJSON);
        // Clear the existing graph (if any)
        Plotly.purge('graphContainer');

        // Create a new Plotly graph on the 'graphContainer'
        Plotly.newPlot('graphContainer', graphJSON.data, graphJSON.layout);
    });
}

/**
 * Handles the update of results.
 *
 * @param {None} None - The function does not accept any parameters.
 * @return {None} None - The function does not return any value.
 */
function handleUpdateResults() {
    const dropdowns = document.querySelectorAll('.dropdown-section select');
    const form = document.getElementById('graphForm');
    const updateButton = document.getElementById('updateResultsButton');
    const goButton = document.querySelector('button[type="submit"]');

    // Disable all dropdowns
    dropdowns.forEach(dropdown => {
        dropdown.disabled = true;
    });

    // Disable the form and show a loading indicator
    form.disabled = true;

    // Disable the "Update Processed Results" button and show a loading indicator
    updateButton.disabled = true;
    updateButton.innerHTML = 'Updating...';

    // Disable the "Go" button
    goButton.disabled = true;

    // Perform an AJAX request to /update_results for updating processed results
    fetch('/update_results', {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        // Re-enable all dropdowns
        dropdowns.forEach(dropdown => {
            dropdown.disabled = false;
        });

        // Re-enable the form and reset its text
        form.disabled = false;

        // Re-enable the "Update Processed Results" button and reset its text
        updateButton.disabled = false;
        updateButton.innerHTML = 'Update Processed Results';

        // Re-enable the "Go" button
        goButton.disabled = false;

        if (data.status === 'success') {
            // Success: Show a success message
            alert('Processed results updated successfully');

            // Update the Ticker dropdown options based on the returned tickers
            const tickerDropdown = document.getElementById('ticker');
            tickerDropdown.innerHTML = '';  // Clear existing options

            data.tickers.forEach(ticker => {
                const option = document.createElement('option');
                option.value = ticker;
                option.textContent = ticker;
                tickerDropdown.appendChild(option);
            });
        } else {
            // Error: Show an error message
            alert('Error updating processed results: ' + data.message);
        }
    })
    .catch(error => {
        // Network or other errors: Show an error message
        alert('Error updating processed results: ' + error.message);

        dropdowns.forEach(dropdown => {
            dropdown.disabled = false;
        });

        form.disabled = false;

        updateButton.disabled = false;
        updateButton.innerHTML = 'Update Processed Results';

        goButton.disabled = false;
    });
}

