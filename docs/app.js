const COLORS = {
  red: '#e10600',
  black: '#15151e',
  gray: '#38383f',
  silver: '#d0d0d2'
};

const BASE_LAYOUT = {
  margin: { l: 60, r: 30, t: 60, b: 70 },
  font: { family: 'Google Sans, sans-serif', color: COLORS.black },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)'
};

const CONFIG = { responsive: true, displayModeBar: false };

function loadJson(path) {
  return fetch(path).then((res) => res.json());
}

function layoutFor(target, extra) {
  const el = document.getElementById(target);
  const rect = el.getBoundingClientRect();
  const height = Math.max(320, Math.floor(rect.height || 0));
  const width = Math.max(320, Math.floor(rect.width || 0));
  return {
    ...BASE_LAYOUT,
    width,
    height,
    ...extra
  };
}

function plotEmpty(target, message) {
  setChartHeight(target, 260);
  const layout = layoutFor(target, {
    xaxis: { visible: false },
    yaxis: { visible: false },
    annotations: [{
      text: message || 'Sin datos disponibles',
      x: 0.5,
      y: 0.5,
      xref: 'paper',
      yref: 'paper',
      showarrow: false,
      font: { size: 14 }
    }]
  });
  Plotly.newPlot(target, [], layout, CONFIG);
}

function setChartHeight(target, height) {
  const el = document.getElementById(target);
  el.style.height = `${height}px`;
}

function barHeightFor(labels) {
  return Math.max(360, labels.length * 28 + 120);
}

function heatmapHeightFor(rows) {
  return Math.max(360, rows.length * 24 + 160);
}

function plotLine(target, x, y, name, title, xLabel, yLabel) {
  if (!x.length) {
    plotEmpty(target);
    return;
  }
  const trace = {
    x,
    y,
    type: 'scatter',
    mode: 'lines+markers',
    name: name || ''
  };
  setChartHeight(target, 420);
  Plotly.newPlot(target, [trace], layoutFor(target, {
    title: { text: title },
    xaxis: { title: xLabel },
    yaxis: { title: yLabel }
  }), CONFIG);
}

function plotBar(target, x, y, orientation, title, xLabel, yLabel) {
  if (!x.length && !y.length) {
    plotEmpty(target);
    return;
  }
  const isHorizontal = orientation === 'h';
  if (isHorizontal) {
    setChartHeight(target, barHeightFor(y));
  } else {
    setChartHeight(target, 420);
  }
  const trace = {
    x,
    y,
    type: 'bar',
    orientation: orientation || 'v',
    marker: { color: COLORS.red }
  };
  const layout = layoutFor(target, {
    title: { text: title },
    xaxis: { title: xLabel, automargin: true },
    yaxis: { title: yLabel, automargin: true }
  });
  Plotly.newPlot(target, [trace], layout, CONFIG);
}

function plotBox(target, traces, title, yLabel) {
  if (!traces.length) {
    plotEmpty(target);
    return;
  }
  setChartHeight(target, 420);
  const data = traces.map((trace) => ({
    y: trace.values,
    name: trace.label,
    type: 'box',
    marker: { color: COLORS.red }
  }));
  Plotly.newPlot(target, data, layoutFor(target, {
    title: { text: title },
    yaxis: { title: yLabel }
  }), CONFIG);
}

function plotHist(target, values, title, xLabel, yLabel) {
  if (!values.length) {
    plotEmpty(target);
    return;
  }
  setChartHeight(target, 420);
  const trace = {
    x: values,
    type: 'histogram',
    marker: { color: COLORS.red }
  };
  Plotly.newPlot(target, [trace], layoutFor(target, {
    title: { text: title },
    xaxis: { title: xLabel },
    yaxis: { title: yLabel }
  }), CONFIG);
}

function plotScatter(target, x, y, trend, title, xLabel, yLabel) {
  if (!x.length || !y.length) {
    plotEmpty(target);
    return;
  }
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
  Plotly.newPlot(target, traces, layoutFor(target, {
    title: { text: title },
    xaxis: { title: xLabel },
    yaxis: { title: yLabel }
  }), CONFIG);
}

function plotHeatmap(target, data, title, xLabel, yLabel) {
  if (!data.teams || !data.teams.length) {
    plotEmpty(target);
    return;
  }
  setChartHeight(target, heatmapHeightFor(data.decades || []));
  const trace = {
    z: data.z,
    x: data.teams,
    y: data.decades,
    type: 'heatmap',
    colorscale: 'Reds'
  };
  const layout = layoutFor(target, {
    title: { text: title },
    xaxis: {
      title: xLabel,
      tickangle: -45,
      automargin: true,
      tickfont: { size: 10 }
    },
    yaxis: { title: yLabel, automargin: true },
    margin: { l: 70, r: 30, t: 60, b: 140 }
  });
  Plotly.newPlot(target, [trace], layout, CONFIG);
}

function plotBarWithCI(target, data, title, xLabel, yLabel) {
  if (!data.decades || !data.decades.length) {
    plotEmpty(target);
    return;
  }
  setChartHeight(target, 420);
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
  Plotly.newPlot(target, [trace], layoutFor(target, {
    title: { text: title },
    xaxis: { title: xLabel },
    yaxis: { title: yLabel }
  }), CONFIG);
}

function plotScatterWithLine(target, x, y, title, xLabel, yLabel) {
  if (!x.length || !y.length) {
    plotEmpty(target);
    return;
  }
  setChartHeight(target, 420);
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
  Plotly.newPlot(target, traces, layoutFor(target, {
    title: { text: title },
    xaxis: { title: xLabel },
    yaxis: { title: yLabel }
  }), CONFIG);
}

function init() {
  loadJson('data/b1_01.json').then((data) => plotLine(
    'chart-b1-01',
    data.years,
    data.pct,
    '',
    'BLOQUE 1 - % victorias equipo dominante',
    'Ano',
    '% victorias'
  ));
  loadJson('data/b1_02.json').then((data) => plotHeatmap(
    'chart-b1-02',
    data,
    'BLOQUE 1 - Share de victorias por decada y equipo',
    'Equipo',
    'Decada'
  ));
  loadJson('data/b1_03a.json').then((data) => plotBar(
    'chart-b1-03a',
    data.values,
    data.labels,
    'h',
    'Pilotos: titulos consecutivos',
    'Titulos',
    'Piloto'
  ));
  loadJson('data/b1_03b.json').then((data) => plotBar(
    'chart-b1-03b',
    data.values,
    data.labels,
    'h',
    'Equipos: titulos consecutivos',
    'Titulos',
    'Equipo'
  ));

  loadJson('data/b2_01.json').then((data) => plotLine(
    'chart-b2-01',
    data.years,
    data.rho,
    '',
    'BLOQUE 2 - Correlacion Grid vs Posicion final',
    'Ano',
    'Rho Spearman'
  ));
  loadJson('data/b2_02.json').then((data) => {
    setChartHeight('chart-b2-02', 420);
    const traces = data.traces.map((trace) => ({
      x: trace.x,
      y: trace.y,
      type: 'scatter',
      mode: 'lines',
      name: String(trace.decade)
    }));
    Plotly.newPlot('chart-b2-02', traces, layoutFor('chart-b2-02', {
      title: { text: 'BLOQUE 2 - Probabilidad de podio por grid (decadas)' },
      xaxis: { title: 'Posicion de salida' },
      yaxis: { title: 'Probabilidad de podio' }
    }), CONFIG);
  });
  loadJson('data/b2_03.json').then((data) => plotBox(
    'chart-b2-03',
    data.traces,
    'BLOQUE 2 - Delta posiciones por decada',
    'Posicion final - grid'
  ));

  loadJson('data/b3_01.json').then((data) => plotScatter(
    'chart-b3-01',
    data.x,
    data.y,
    data.trend,
    'BLOQUE 3 - Pit time vs posicion final',
    'Tiempo total en boxes (s)',
    'Posicion final'
  ));
  loadJson('data/b3_02.json').then((data) => plotBarWithCI(
    'chart-b3-02',
    data,
    'BLOQUE 3 - Efecto marginal por decada',
    'Decada',
    'Delta posiciones por +1s'
  ));
  loadJson('data/b3_03.json').then((data) => plotHist(
    'chart-b3-03',
    data.values,
    'BLOQUE 3 - Errores graves en boxes',
    'Duracion de parada (s)',
    'Frecuencia'
  ));

  loadJson('data/b4_01.json').then((data) => plotBar(
    'chart-b4-01',
    data.years,
    data.pct,
    'v',
    'BLOQUE 4 - % puntos del mundial procedentes del sprint',
    'Ano',
    '% puntos sprint'
  ));
  loadJson('data/b4_02.json').then((data) => plotHist(
    'chart-b4-02',
    data.values,
    'BLOQUE 4 - Cambios de posicion inducidos por sprint',
    'Delta posicion',
    'Frecuencia'
  ));
  loadJson('data/b4_03.json').then((data) => {
    setChartHeight('chart-b4-03', 420);
    const traces = [
      { label: 'Con sprint', values: data.sprint },
      { label: 'Sin sprint', values: data.nonsprint }
    ];
    plotBox('chart-b4-03', traces, 'BLOQUE 4 - Imprevisibilidad sprint vs no sprint', 'Varianza top-10');
  });
  loadJson('data/b4_04.json').then((data) => plotScatterWithLine(
    'chart-b4-04',
    data.margins,
    data.impacts,
    'BLOQUE 4 - Sprint y campeonatos decididos',
    'Margen final',
    'Impacto sprint'
  ));
}

window.addEventListener('DOMContentLoaded', init);
window.addEventListener('resize', () => {
  document.querySelectorAll('.chart').forEach((el) => {
    if (el.data) {
      Plotly.Plots.resize(el);
    }
  });
});
