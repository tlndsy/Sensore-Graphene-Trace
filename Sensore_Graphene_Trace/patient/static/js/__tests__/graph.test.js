const {
  formatMetricName,
  plotGraph,
  showMetric,
  updateMetrics,
  showTimeRange,
  toggleLiveMode
} = require("../graph");

// Plotly configuration
global.Plotly = {
  react: jest.fn(),
  restyle: jest.fn(),
  relayout: jest.fn(),
  extendTraces: jest.fn()
};

// Testing data
beforeEach(() => {
    jest.resetModules();
  document.body.innerHTML = `
    <div id="graph"></div>
    <div id="peak-pressure"></div>
    <div id="contact-area"></div>
    <div id="coefficient-of-variation"></div>
    <button id="live-toggle">Live Mode</button>`;

  global.times = ["2026-01-01T10:00:00", "2026-01-01T10:00:01", "2026-01-01T10:00:02"];
  global.peak_pressure_index = [1.111, 2.222, 3.333];
  global.contact_area_percent = [10.1, 20.2, 30.3];
  global.coefficient_of_variation = [5.5, 6.6, 7.7];
  global.window = global;

  jest.clearAllMocks();
  jest.clearAllTimers();
  jest.useRealTimers();

  global.isLive = false;
  global.index = 0;
  global.liveInterval = null;
});

// Tests
describe("Graph utilities", () => {

  // Tests that underscores are removed from the string so that they can be presented as graph titles
  test("formatMetricName formats correctly", () => {
    expect(formatMetricName("peak_pressure_index"))
      .toBe("peak pressure index");
    expect(formatMetricName("contact_area_percent"))
      .toBe("contact area percent");
  });

  // Tests that Plotly.react gets called to plot the graph once
  test("plotGraph calls Plotly.react", () => {
    plotGraph([1, 2, 3], "peak_pressure_index", times);
    expect(Plotly.react).toHaveBeenCalledTimes(1);
  });

  // Tests that the metrics update on the graph when the showMetric() function is called
  test("showMetric updates Plotly visibility and layout", () => {
    showMetric("peak_pressure_index", 0, "peak_pressure_index");
    expect(Plotly.restyle).toHaveBeenCalled();
    expect(Plotly.relayout).toHaveBeenCalledWith("graph", { "yaxis.title.text": "peak pressure" });
  });

  // Tests that metrics are displayed correctly to the user upon updateMetrics() being called
  test("updateMetrics updates DOM values correctly", () => {
    updateMetrics(1);
    expect(document.getElementById("peak-pressure").textContent)
      .toBe("Peak pressure: 2.22");
    expect(document.getElementById("contact-area").textContent)
      .toBe("Contact area: 20.20%");
    expect(document.getElementById("coefficient-of-variation").textContent)
      .toBe("Coefficient of variation: 6.60%");
  });

  // Tests that the user can customise the length of data they are displayed by time
  test("showTimeRange filters data and calls Plotly.react", () => {
    showTimeRange(1000);
    expect(Plotly.react).toHaveBeenCalled();
  });

  // Tests that live mode begins displaying the user's live graph data and it updates each second
  test("toggleLiveMode starts and updates graph", () => {
    jest.useFakeTimers();
    const button = document.getElementById("live-toggle");
    toggleLiveMode(); // start live mode
    expect(button.textContent).toBe("Stop Live");
    jest.advanceTimersByTime(1000);
    expect(Plotly.extendTraces).toHaveBeenCalled();
    jest.useRealTimers();
  });

  // Tests that the user can pause their live data when pressing the stop live mode button
  test("toggleLiveMode stops live mode when toggled again", () => {
    const button = document.getElementById("live-toggle");
    toggleLiveMode(); // start
    toggleLiveMode(); // stop
    expect(button.textContent).toBe("Live Mode");
  });

});