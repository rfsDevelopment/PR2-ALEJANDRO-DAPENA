const COLORS = {
  red: '#e10600',
  black: '#15151e',
  gray: '#38383f',
  silver: '#d0d0d2'
};

const BASE_LAYOUT = {
  margin: { l: 50, r: 30, t: 30, b: 50 },
  font: { family: 'Google Sans, sans-serif', color: COLORS.black },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)'
};

const CONFIG = { responsive: true, displayModeBar: false };

function loadJson(path) {
  return fetch(path).then((res) => res.json());
}

function plotLine(target, x, y, name) {
  const trace = {
    x,
    y,
    type: 'scatter',
    mode: 'lines+markers',
    name: name || ''
  };
  Plotly.newPlot(target, [trace], BASE_LAYOUT, CONFIG);
}

function plotBar(target, x, y, orientation) {
  const trace = {
    x,
    y,
    type: 'bar',
    orientation: orientation || 'v',
    marker: { color: COLORS.red }
  };
  Plotly.newPlot(target, [trace], BASE_LAYOUT, CONFIG);
}

function plotBox(target, traces) {
  const data = traces.map((trace) => ({
    y: trace.values,
    name: trace.label,
    type: 'box',
    marker: { color: COLORS.red }
  }));
  Plotly.newPlot(target, data, BASE_LAYOUT, CONFIG);
}

function plotHist(target, values) {
  const trace = {
    x: values,
    type: 'histogram',
    marker: { color: COLORS.red }
  };
  Plotly.newPlot(target, [trace], BASE_LAYOUT, CONFIG);
}

function plotScatter(target, x, y, trend) {
  const traces = [{
    x,
    y,
    type: 'scatter',
    mode: 'markers',
    marker: { color: COLORS.red }
  }];
  if (trend && x.length > 1) {
    const minX = Math.min(...x);
    const maxX = Math.max(...x);
    const xLine = [minX, maxX];
    const yLine = xLine.map((val) => trend.slope * val + trend.intercept);
    traces.push({
      x: xLine,
      y: yLine,
      type: 'scatter',
      mode: 'lines',
      line: { color: COLORS.black }
    });
  }
  Plotly.newPlot(target, traces, BASE_LAYOUT, CONFIG);
}

function plotHeatmap(target, data) {
  const trace = {
    z: data.z,
    x: data.teams,
    y: data.decades,
    type: 'heatmap',
    colorscale: 'Reds'
  };
  const layout = {
    ...BASE_LAYOUT,
    xaxis: { tickangle: -45 }
  };
  Plotly.newPlot(target, [trace], layout, CONFIG);
}

function plotBarWithCI(target, data) {
  const trace = {
    x: data.decades,
    y: data.coefs,
    type: 'bar',
    marker: { color: COLORS.red },
    error_y: data.ci_low && data.ci_high ? {
      type: 'data',
      array: data.ci_high.map((v, i) => v - data.coefs[i]),
      arrayminus: data.ci_low.map((v, i) => data.coefs[i] - v),
      visible: true
    } : undefined
  };
  Plotly.newPlot(target, [trace], BASE_LAYOUT, CONFIG);
}

function plotScatterWithLine(target, x, y) {
  const maxVal = Math.max(0, ...x, ...y);
  const minVal = Math.min(0, ...x, ...y);
  const traces = [
    {
      x,
      y,
      type: 'scatter',
      mode: 'markers',
      marker: { color: COLORS.red }
    },
    {
      x: [minVal, maxVal],
      y: [minVal, maxVal],
      type: 'scatter',
      mode: 'lines',
      line: { color: COLORS.black, dash: 'dash' },
      hoverinfo: 'skip'
    }
  ];
  Plotly.newPlot(target, traces, BASE_LAYOUT, CONFIG);
}

function init() {
  loadJson('data/b1_01.json').then((data) => plotLine('chart-b1-01', data.years, data.pct));
  loadJson('data/b1_02.json').then((data) => plotHeatmap('chart-b1-02', data));
  loadJson('data/b1_03a.json').then((data) => plotBar('chart-b1-03a', data.values, data.labels, 'h'));
  loadJson('data/b1_03b.json').then((data) => plotBar('chart-b1-03b', data.values, data.labels, 'h'));

  loadJson('data/b2_01.json').then((data) => plotLine('chart-b2-01', data.years, data.rho));
  loadJson('data/b2_02.json').then((data) => {
    const traces = data.traces.map((trace) => ({
      x: trace.x,
      y: trace.y,
      type: 'scatter',
      mode: 'lines',
      name: String(trace.decade)
    }));
    Plotly.newPlot('chart-b2-02', traces, BASE_LAYOUT, CONFIG);
  });
  loadJson('data/b2_03.json').then((data) => plotBox('chart-b2-03', data.traces));

  loadJson('data/b3_01.json').then((data) => plotScatter('chart-b3-01', data.x, data.y, data.trend));
  loadJson('data/b3_02.json').then((data) => plotBarWithCI('chart-b3-02', data));
  loadJson('data/b3_03.json').then((data) => plotHist('chart-b3-03', data.values));

  loadJson('data/b4_01.json').then((data) => plotBar('chart-b4-01', data.years, data.pct));
  loadJson('data/b4_02.json').then((data) => plotHist('chart-b4-02', data.values));
  loadJson('data/b4_03.json').then((data) => {
    const traces = [
      { label: 'Con sprint', values: data.sprint },
      { label: 'Sin sprint', values: data.nonsprint }
    ];
    plotBox('chart-b4-03', traces);
  });
  loadJson('data/b4_04.json').then((data) => plotScatterWithLine('chart-b4-04', data.margins, data.impacts));
}

window.addEventListener('DOMContentLoaded', init);
