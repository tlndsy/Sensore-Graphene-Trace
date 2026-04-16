const heatmap_layout = {
    margin: {t: 1, l: 1, r: 1, b: 1},
    xaxis: {visible: false},
    yaxis: {visible: false, autorange: 'reversed'},
    line: {color: "#ccc"},
    linewidth: 1
};
const heatmap_config = {staticPlot: false, displayModeBar: false, responsive: true}

function listToMatrix(flat_list) {
    const size = Math.sqrt(flat_list.length) // Defines matrix size
    return Array.from({length: size}, (_, i) => flat_list.slice(i * size, i * size + size));
} // Return matrix

// For displaying the predicted regions of concern (currently just displays heatmap)
function plotHeatmap(pressure_matrix) {
    Plotly.newPlot('heatmap', [{
        z: pressure_matrix,
        type: 'heatmap',
        showscale: false
    }], heatmap_layout, heatmap_config);
}

// Simulates live heatmap
function simulateHeatMap() {
    let frame = 0;
    const interval = setInterval(() => {
        if (frame >= pressure_frames.length) {
            clearInterval(interval);
            return;
        }
        const matrix = listToMatrix(pressure_frames[frame]);
        Plotly.react('heatmap', [{z: matrix, type: 'heatmap', showscale: false}], heatmap_layout, heatmap_config);
        frame++;
    }, 1000 / 15)
}

module.exports = {
    listToMatrix,
    plotHeatmap,
    simulateHeatMap
};