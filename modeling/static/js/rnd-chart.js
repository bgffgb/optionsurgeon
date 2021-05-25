$(document).ready(function() {
N = 50;
var data = d3.range(N).map(function(i) {
  return{
    x : i*1/N,
    y : i*1/N,
  }; 
});

var svg = d3.select("svg").attr("width", 620).attr("height", 480);
var margin = {top: 20, right: 20, bottom: 30, left: 50},
  width = svg.attr("width") - margin.left - margin.right,
  height = svg.attr("height") - margin.top - margin.bottom,
  g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

console.log(width, height, svg.attr("width"), svg.attr("height"));

var x = d3.scaleLinear().range([0, width])
.domain([0, d3.max(data, function(d) { return d.x; })]);

var y = d3.scaleLinear().range([height, 0])
.domain([0, d3.max(data, function(d) { return d.y; })]);

var area = d3.area()
  .curve(d3.curveMonotoneX)
  .x(function(d) { return x(d.x); })
  .y0(y(0))
  .y1(function(d) { return y(d.y); });

g.append("g")
  .attr("class", "axis axis--x")
  .attr("transform", "translate(0," + height + ")")
  .call(d3.axisBottom(x));

g.append("g")
  .attr("class", "axis axis--y")
  .call(d3.axisLeft(y))
  .append("text")
  .attr("transform", "rotate(-90)")
  .attr("y", 6)
  .attr("dy", "0.71em")
  .attr("fill", "#000")
  .text("Probability");

var source = g.selectAll(".area")
.data(data)
.enter().append("g")
.attr("fill", "steelblue")
.attr("d", area);

svg.append("path")
  .datum(data)
  .attr("fill", "steelblue")
  .attr("d", area)
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
});
