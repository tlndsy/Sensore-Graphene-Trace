const {
  listToMatrix,
  plotHeatmap,
  simulateHeatMap
} = require("../heatmap");
// Plotly
global.Plotly = {newPlot: jest.fn(), react: jest.fn()};

beforeEach(() => {
  document.body.innerHTML = `<div id="heatmap"></div>`;jest.clearAllMocks();jest.useRealTimers();});

//  Tests
describe("Heatmap utilities", () => {

  test("listToMatrix converts flat list to square matrix", () => {
    const flat = [1,2,3,4];
    const matrix = listToMatrix(flat);
    expect(matrix).toEqual([[1,2], [3,4]]);
  });

  test("listToMatrix works for larger square lists", () => {
    const flat = [1,2,3,4,5,6,7,8,9];
    const matrix = listToMatrix(flat);
    expect(matrix).toEqual([[1,2,3], [4,5,6], [7,8,9]]);
  });

  test("plotHeatmap calls Plotly.newPlot with correct data", () => {
    const matrix = [[1,2], [3,4]];
    plotHeatmap(matrix);
    expect(Plotly.newPlot).toHaveBeenCalledTimes(1);
    const callArgs = Plotly.newPlot.mock.calls[0];
    expect(callArgs[0]).toBe("heatmap"); // element id
    expect(callArgs[1][0].z).toEqual(matrix); // heatmap data
  });

  test("simulateHeatMap updates heatmap frames over time", () => {
    jest.useFakeTimers();
    global.pressure_frames = [[1,2,3,4], [5,6,7,8]];
    simulateHeatMap();
    jest.advanceTimersByTime(1000/15);
    expect(Plotly.react).toHaveBeenCalled();
    jest.useRealTimers();
  });

  test("simulateHeatMap stops when frames finish", () => {
    jest.useFakeTimers();
    global.pressure_frames = [[1,2,3,4]];
    simulateHeatMap();
    jest.advanceTimersByTime(2000);
    expect(Plotly.react).toHaveBeenCalledTimes(1);
    jest.useRealTimers();
  });

});