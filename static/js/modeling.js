const gradientResetPercentage = "10%";
const base_color_off = "rgba(220, 20, 60, 0.3)";
const base_color_on = "rgba(220, 20, 60, 0.7)";
const mod_color_off = "rgba(20, 220, 220, 0.3)";
const mod_color_on = "rgba(20, 220, 220, 0.7)";

var portfolio_data, portfolio_strikes, last_mode="E";

$(document).ready(function() {
  chart_elem = document.getElementById("chartdiv");
  if (chart_elem === null) {
    return;
  }

  document.getElementById("portfoliodiv").style.display = "none";

  const csrftoken = getCookie('csrftoken');
  var shift_commands = ["mean_up", "mean_down", "var_up", "var_down", "reset"];
  var portfolio_commands = ["callinc", "calldec", "putinc", "putdec"];
  update_tables();

  function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
    }
  });

  $("button").click(function(e) {
    var bval = $(this).val();
    if (bval === "sync") {
      e.preventDefault();
      $.ajax({
        type: "POST",
        url: "sync",
        data: {
            "ticker": ticker,
            "ticker_type": ticker_type,
            "expiry": expiry,
            "callqty" : callqty,
            "putqty" : putqty,
            "mean_level" : mean_level,
            "var_level" : var_level,
        },
        success: function(result) {
            callchain = result["callchain"];
            putchain = result["putchain"];

            rnd_data = result["chart"];
            rnd_modded = result["chart_modded"];          
            render_rnd_charts();
            update_tables();
            update_timestamp(result["datetime"]);

            portfolio_data = result["portfoliochart"];
            portfolio_strikes = result["strikes"];
            portfolio_label = result["portfolio_label"];
            portfolio_qty = result["portfolio_qty"];
            expr = result["expr"];
            winp = result["winp"];
            totcost = result["totcost"];
            chart = portfolio_data;
            strikes = portfolio_strikes;
            update_portfolio(portfolio_qty, portfolio_label, expr, winp, totcost);
        },
        error: function(result) {
            console.log('Uh Oh. Chart update error:', result);
        }
      });
    }
    if (bval === "toggle") {
      e.preventDefault();
      if (last_mode === "E") {
        last_mode = "PE";
        $(this).find('i').removeClass('fa-toggle-off').toggleClass('fa-toggle-on');
      } else {
        last_mode = "E";
        $(this).find('i').removeClass('fa-toggle-on').toggleClass('fa-toggle-off');
      }
      render_portfolio_charts(last_mode);
    }
    if (shift_commands.includes(bval)) {
      e.preventDefault();
      if (bval === "mean_up") {
        mean_level += 1;
      } else  if (bval === "mean_down") {
        mean_level -= 1;
      } else  if (bval === "var_up") {
        var_level += 1;
      } else  if (bval === "var_down") {
        var_level -= 1;
      } else if  (bval === "reset") {
        mean_level = 0;
        var_level = 0;
      }
      $.ajax({
        type: "POST",
        url: "update_chart",
        data: {
            "ticker": ticker,
            "expiry": expiry,
            "callchain" : JSON.stringify(callchain),
            "putchain" : JSON.stringify(putchain),
            "callqty" : callqty,
            "putqty" : putqty,
            "mean_level" : mean_level,
            "var_level" : var_level,
            "distrib_params" : distrib_params
        },
        success: function(result) {
            rnd_data = result["chart"];
            rnd_modded = result["chart_modded"];
            callchain = result["callchain"];
            putchain = result["putchain"];
            render_rnd_charts();
            update_tables();

            portfolio_data = result["portfoliochart"];
            portfolio_strikes = result["strikes"];
            portfolio_label = result["portfolio_label"];
            portfolio_qty = result["portfolio_qty"];
            expr = result["expr"];
            winp = result["winp"];
            totcost = result["totcost"];
            chart = portfolio_data;
            strikes = portfolio_strikes;
            update_portfolio(portfolio_qty, portfolio_label, expr, winp, totcost);
        },
        error: function(result) {
            console.log('Uh Oh. Chart update error:', result);
        }
      });
    }

    if (portfolio_commands.includes(bval)) {
      e.preventDefault();
      index = $(this)[0].name;      
      if (bval === "callinc" || bval === "calldec") {
        if (bval === "callinc") {
          callqty[index] += 1;
        } else {
          callqty[index] -= 1;
        }
        el = document.getElementById("c"+index)
        el.innerHTML = callqty[index];
      } else if (bval === "putinc" || bval === "putdec") {
        if (bval === "putinc") {
          putqty[index] += 1;
        } else {
          putqty[index] -= 1;
        }
        el = document.getElementById("p"+index)
        el.innerHTML = putqty[index];
      }

      $.ajax({
        type: "POST",
        url: "update_portfolio",
        data: {
            "ticker": ticker,
            "expiry": expiry,
            "callchain" : JSON.stringify(callchain),
            "putchain" : JSON.stringify(putchain),
            "callqty" : callqty,
            "putqty" : putqty,
            "mean_level" : mean_level,
            "var_level" : var_level,
            "distrib_params" : distrib_params
        },
        success: function(result) {
            portfolio_data = result["portfoliochart"];
            portfolio_strikes = result["strikes"];
            portfolio_label = result["portfolio_label"];
            portfolio_qty = result["portfolio_qty"];
            expr = result["expr"];
            winp = result["winp"];
            totcost = result["totcost"];
            update_portfolio(portfolio_qty, portfolio_label, expr, winp, totcost);
        },
        error: function(result) {
            console.log('Uh Oh. Portfolio update error:', result);
        }
      });
    }
  });

  render_rnd_charts();
});

function highlight(obj){
   var orig = obj.style.backgroundColor;
   obj.style.backgroundColor = "gray";
   setTimeout(function(){
        obj.style.backgroundColor = orig;
   }, 1000);
}

function update_timestamp(datetime) {
  new_text = "Last updated: " + datetime + ", New York time (15 minutes delayed)"
  label = document.getElementById("calltimestamp");
  label.textContent = new_text;
  label = document.getElementById("puttimestamp");
  label.textContent = new_text;
}

function update_portfolio(qty, label, expr, winp, totcost) {
  portfoliodiv = document.getElementById("portfoliodiv");
  portfoliotext = document.getElementById("portfoliotext");
  if (qty.length === 0) {
    portfoliodiv.style.display = "none";
    portfoliotext.style.display = "flex";
  } else {
    portfoliodiv.style.display = "flex";
    portfoliotext.style.display = "none";
    $("#portfoliotable tbody tr").remove();
    tbodyRef = document.getElementById('portfoliotable').getElementsByTagName('tbody')[0];
    for (let i = 0; i < qty.length; i++){
      newRow = tbodyRef.insertRow();
      newCell = newRow.insertCell();
      newText = document.createTextNode(qty[i]);
      newCell.appendChild(newText);
      newCell = newRow.insertCell();
      newText = document.createTextNode(label[i]);
      newCell.appendChild(newText);
    }
    exprtxt = document.getElementById("expr");
    exprtxt.innerHTML = expr;
    winptxt = document.getElementById("winp");
    winptxt.innerHTML = winp + "%";
    winptxt = document.getElementById("totcost");
    winptxt.innerHTML = totcost;
    
    render_portfolio_charts(last_mode);
  }
}

function trim_sharpe(val){
  if (val < -10) {
    return "-10+";
  } else if (val > 10) {
    return "10+";
  }
  return val;
}

function update_tables() {
  call_table = document.getElementById("calltable");
  for(let i = 0; i < callchain.length; i++){
    for (let j=0; j<6; j++){
      cell = call_table.rows[i + 1].cells[j + 1];
      cell.innerHTML = callchain[i][j].toFixed(2);
    }    
    expected = call_table.rows[i + 1].cells[7];
    expected.innerHTML = callchain[i][6].toFixed(2)+"%";
    sharpe = call_table.rows[i + 1].cells[8];
    sharpe.innerHTML = trim_sharpe(callchain[i][7].toFixed(2));
    if (callchain[i][6] >= 0) {
      expected.style.color = "green";
      sharpe.style.color = "green";
    } else {
      expected.style.color = "red";
      sharpe.style.color = "red";
    }
  }
  put_table = document.getElementById("puttable");  
  for(let i = 0; i < putchain.length; i++){
    for (let j=0; j<6; j++){
      cell = put_table.rows[i + 1].cells[j + 1];
      cell.innerHTML = putchain[i][j].toFixed(2);
    }
    expected = put_table.rows[i + 1].cells[7];
    expected.innerHTML = putchain[i][6].toFixed(2)+"%";
    sharpe = put_table.rows[i + 1].cells[8];    
    sharpe.innerHTML = trim_sharpe(putchain[i][7].toFixed(2));
    if (putchain[i][6] >= 0) {
      expected.style.color = "green";
      sharpe.style.color = "green";
    } else {
      expected.style.color = "red";
      sharpe.style.color = "red";
    }
  }
}

function render_portfolio_charts(mode) {
  var margin = {top: 20, right: 20, bottom: 30, left: 50};
  chart_elem = document.getElementById("portfoliochartdiv");
  width = chart_elem.offsetWidth - margin.left - margin.right;
  height = Math.max(chart_elem.offsetHeight, 500) - margin.top - margin.bottom;
  last_mode = mode;

  d3.select("#portfoliochartdiv").selectAll("*").remove();

  var svg = d3.select("#portfoliochartdiv").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);
  var g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var x = d3.scaleLinear().range([0, width])
    .domain([d3.min(portfolio_data, function(d) { return d.x; }),
             d3.max(portfolio_data, function(d) { return d.x; })]);
  if (mode === "E") {
    var y = d3.scaleLinear().range([height, 0])
      .domain([d3.min(portfolio_data, function(d) { return d.e; }), 
               d3.max(portfolio_data, function(d) { return d.e; })]);
  } else {
    var y = d3.scaleLinear().range([height, 0])
      .domain([d3.min(portfolio_data, function(d) { return d.pe; }), 
               d3.max(portfolio_data, function(d) { return d.pe; })]);
  }

  g.append("g")
    .attr("class", "axis axis--x")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x))
    .append("text")
    .attr("x", width / 2)
    .attr("y", margin.bottom * 0.9)
    .attr("fill", "#000")
    .text("Price at expiration");
  
  if (mode === "E") {
    ylabel = "Return";
  } else {
    ylabel = "Return * Probability";
  }

  g.append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisLeft(y))
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", - height / 2 + margin.bottom)
    .attr("y", - margin.left * 0.85)
    .attr("fill", "#000")
    .text(ylabel);

  g.append("path")
    .datum(portfolio_data)
    .attr("fill", "none")
    .attr("stroke", mod_color_on)
    .attr("stroke-width", 1.5)
    .attr("d", d3.line()
      .x(function(d) { return x(d.x); })
      .y(function(d) { if (mode === "E") {return y(d.e);} else {return y(d.pe); } })
    )

    var Tooltip = d3.select("#portfoliochartdiv")
      .append("div")
      .style("opacity", 0)
      .attr("class", "tooltip")
      .style("background-color", "white")
      .style("border", "solid")
      .style("border-width", "2px")
      .style("border-radius", "5px")
      .style("padding", "5px")

      var mouseover = function(d) {
        Tooltip
          .style("opacity", 1)
      }
      var mousemove = function(d) {
        Tooltip
          .html("Strike " + d.x + "<br>Return " + d.e)
          .style("left", (d3.mouse(this)[0]+70) + "px")
          .style("top", (d3.mouse(this)[1]) + "px")
      }
      var mouseleave = function(d) {
        Tooltip
          .style("opacity", 0)
      }

    g.append("g")
      .selectAll("dot")
      .data(portfolio_strikes)
      .enter()
      .append("circle")
        .attr("class", "myCircle")
        .attr("cx", function(d) { return x(d.x) } )
        .attr("cy", function(d) { if (mode === "E") {return y(d.e);} else {return y(d.pe);}} )
        .attr("r", 6)
        .attr("stroke", mod_color_on)
        .attr("fill", mod_color_on)
        .attr("stroke-width", 3)
        .on("mouseover", mouseover)
        .on("mousemove", mousemove)
        .on("mouseleave", mouseleave)
}

function render_rnd_charts() {
  var margin = {top: 20, right: 20, bottom: 30, left: 50};
  chart_elem = document.getElementById("chartdiv");
  width = chart_elem.offsetWidth - margin.left - margin.right;
  height = Math.max(chart_elem.offsetHeight, 500) - margin.top - margin.bottom;

  d3.select("#chartdiv").selectAll("*").remove();

  var svg = d3.select("#chartdiv").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);
  var g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var x = d3.scaleLinear().range([0, width])
    .domain([d3.min(rnd_data, function(d) { return d.x; }),
             d3.max(rnd_data, function(d) { return d.x; })]);

  var y = d3.scaleLinear().range([height, 0])
    .domain([0, Math.max(d3.max(rnd_data, function(d) { return d.y; }),
                d3.max(rnd_modded, function(d) { return d.y; }))]); 

  var area = d3.area()
    .curve(d3.curveMonotoneX)
    .x(function(d) { return x(d.x); })
    .y0(y(0))
    .y1(function(d) { return y(d.y); });

  g.append("g")
    .attr("class", "axis axis--x")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x))
    .append("text")
    .attr("x", width / 2)
    .attr("y", margin.bottom * 0.9)
    .attr("fill", "#000")
    .text("Price at Expiration");

  
  g.append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisLeft(y))
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", - height / 2 + margin.bottom)
    .attr("y", - margin.left * 0.85)
    .attr("fill", "#000")
    .text("Probability");
  

  draw_plot(rnd_data, "url(#svgGradient)");
  draw_plot(rnd_modded, "url(#svgGradientMod)");

  const defs = svg.append("defs");
  const gradient = defs.append("linearGradient").attr("id", "svgGradient");
  const gradient_mod = defs.append("linearGradient").attr("id", "svgGradientMod");

  gradient_append(gradient, base_color_off, base_color_on);
  gradient_append(gradient_mod, mod_color_off, mod_color_on);

  const bisectX = d3.bisector(dataPoint => dataPoint.x).left;

  function draw_plot(rnd_data, svg_grad) {
    var source = g.selectAll(".area")
      .data(rnd_data)
      .enter().append("g")
      .attr("d", area);

    svg.append("path")
      .datum(rnd_data)
      .style("fill", svg_grad)
      .attr("d", area)
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
      .on("mouseover", handleMouseOver)
      .on("mousemove", handleMouseMove)
      .on('mouseout', handleMouseOut);
  }

  function gradient_append(grad, coloroff, coloron) {  
    grad
      .append("stop")
      .attr("class", "start")
      .attr("offset", gradientResetPercentage)
      .attr("stop-color", coloroff);

    grad
      .append("stop")
      .attr("class", "start")
      .attr("offset", gradientResetPercentage)
      .attr("stop-color", coloron);

    grad
      .append("stop")
      .attr("class", "end")
      .attr("offset", gradientResetPercentage)
      .attr("stop-color", coloron)
      .attr("stop-opacity", 1);

    grad
      .append("stop")
      .attr("class", "end")
      .attr("offset", gradientResetPercentage)
      .attr("stop-color", coloroff);
  }

  var tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

  cx = 70;
  cy1 = 30;
  cy2 = 60;
  svg.append("circle").attr("cx",cx).attr("cy",cy1).attr("r", 6).style("fill", base_color_on);
  svg.append("circle").attr("cx",cx).attr("cy",cy2).attr("r", 6).style("fill", mod_color_on);
  svg.append("text").attr("x", cx + 20).attr("y", cy1 + 5).text("Risk Neutral distribution")
    .style("font-size", "15px").attr("alignment-baseline","middle")
  svg.append("text").attr("x", cx + 20).attr("y", cy2 + 5).text("Predicted distribution")
    .style("font-size", "15px").attr("alignment-baseline","middle")

  function handleMouseOver(data) {
    tooltip
      .style("opacity", 1)
  }

  function handleMouseMove(data) {

    const currentXPosition = d3.mouse(this)[0];
    const xValue = x.invert(currentXPosition);
    const dataIndex = bisectX(data, xValue, 1);
    const leftData = data[0];
    const rightData = data[dataIndex];
    subrndp = 0;
    subrndmodp = 0;
    for (let j=0; j<dataIndex; j++){
      subrndp += parseFloat(rnd_data[j].c);
      subrndmodp += parseFloat(rnd_modded[j].c);
    }
    const x1Percentage = x(leftData.x) / width * 100;
    const x2Percentage = x(rightData.x) / width * 100;
    d3.selectAll(".start").attr("offset", `${x1Percentage}%`);
    d3.selectAll(".end").attr("offset", `${x2Percentage}%`);

    tooltip
      .html("RND "+subrndp.toFixed(2)+"%<br>Predicted "+subrndmodp.toFixed(2)+"%")
      .style("left", (d3.event.pageX + 20) + "px")
      .style("top", (d3.event.pageY) + "px")
      .style("color", "#273746")
  }

  function handleMouseOut() {
    tooltip
      .style("opacity", 0);

    d3.selectAll(".start").attr("offset", gradientResetPercentage);
    d3.selectAll(".end").attr("offset", gradientResetPercentage);
    d3.select('.year1').text('');
    d3.select('.year2').text('')
  }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
