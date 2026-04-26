const date = (typeof times !== "undefined" && times.length) ? new Date(times[0]).toLocaleDateString() : "";

// Presets for plotting the graph
const graph_layout = {
    margin: {t: 1, l: 50, r: 1, b: 50},
    xaxis: {tickformat: "%H:%M", showline: true, line: {color: "#ccc"}, linewidth: 1, mirror: true},
    yaxis: {title: {text: "Peak Pressure Index"}, showline: true, line: {color: "#ccc"}, linewidth: 1, mirror: true}
};
const graph_config = {responsive: true, displayModeBar: false, staticPlot: false};
const graph_traces = [{x: [], y: [], name: "Peak Pressure", mode: "lines", line: {color: '#ccc'}}, {
    x: [],
    y: [],
    name: "Contact Area",
    mode: "lines",
    visible: false
}, {x: [], y: [], name: "Coefficient of Variation", mode: "lines", visible: false}];
let liveInterval = null;
let isLive = false;
let current_metric = "peak_pressure_index";
let index = 0;
const metrics = {peak_pressure_index: 0, contact_area_percent: 1, coefficient_of_variation: 2};
const last_index = (typeof peak_pressure_index !== "undefined") ? peak_pressure_index.length - 1 : 0;

// Graph plotting function
function plotGraph(y, label, times) {
    Plotly.react('graph', [{x: times, y: y, name: formatMetricName(label)}], graph_layout, graph_config);
}

// Displays the metric on the graph that the user selects with a button press
function showMetric(metric, index, label) {
    current_metric = metric;
    Plotly.restyle('graph', {visible: [false, false, false]});
    Plotly.restyle('graph', {visible: true}, [index]);
    Plotly.relayout('graph', {'yaxis.title.text': formatMetricName(label)});
}

// For removing underscores from titles and replacing them with spaces
function formatMetricName(metric) {
    return metric.replace(/_/g, " ").replace("index", "").trim();
}

// Updates the metric value on the switch metric buttons
function updateMetrics(index) {
    document.getElementById("peak-pressure").textContent = `Peak pressure: ${peak_pressure_index[index].toFixed(2)}`;
    document.getElementById("contact-area").textContent = `Contact area: ${contact_area_percent[index].toFixed(2)}%`;
    document.getElementById("coefficient-of-variation").textContent = `Coefficient of variation: ${coefficient_of_variation[index].toFixed(2)}%`;
}

// Displays latest data within a specified timerange in seconds
function showTimeRange(seconds) {
    const latest_timestamp = new Date(times[times.length - 1]);
    const time_range = [];
    const metric_arrays = {peak_pressure_index: [], contact_area_percent: [], coefficient_of_variation: []};

    times.forEach((t, i) => {
        if ((latest_timestamp - new Date(t)) / 1000 <= seconds) {
            time_range.push(t);
            for (const metric in metric_arrays) {
                metric_arrays[metric].push(window[metric][i]);
            }
        }
    });

    const graph_traces = Object.entries(metric_arrays).map(([metric, values]) => ({
        x: time_range, y: values, name: formatMetricName(metric), mode: "lines", visible: metric === current_metric
    }));
    Plotly.react('graph', graph_traces, graph_layout, graph_config);

    // Update latest metric values
    const last_index = time_range.length - 1;
    updateMetrics(last_index);
}

// Used to simulate real time display of the users metrics on the graph
function toggleLiveMode() {
    // Turn off live mode on button press
    const button = document.getElementById("live-toggle") || {textContent: ""};
    if (isLive) {
        if (liveInterval) clearInterval(liveInterval);
        isLive = false;
        button.textContent = "Live Mode";
        return;
    }

    // Turn on live mode on button press
    isLive = true;
    button.textContent = "Stop Live";
    index = 0;
    const graph_traces = Object.keys(metrics).map(metric => ({
        x: [], y: [], name: formatMetricName(metric), mode: "lines", visible: metric === current_metric
    }));
    Plotly.react('graph', graph_traces, graph_layout, graph_config);

    // Runs until the file ends, updates one second at a time
    liveInterval = setInterval(() => {
        if (index >= peak_pressure_index.length) {
            clearInterval(liveInterval);
            isLive = false;
            button.textContent = "Live Mode";
            return;
        }
        const metric_array = window[current_metric];
        const trace_index = metrics[current_metric];
        Plotly.extendTraces('graph', {x: [[times[index]]], y: [[metric_array[index]]]}, [trace_index]);
        updateMetrics(index);
        index++;
    }, 1000);
}

// Export for test functions
module.exports = {
    plotGraph, showMetric, formatMetricName, updateMetrics, showTimeRange, toggleLiveMode
};