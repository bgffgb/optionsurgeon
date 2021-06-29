const grp="10%",bof="rgba(220, 20, 60, 0.3)",bon="rgba(220, 20, 60, 0.7)",mof="rgba(20, 220, 220, 0.3)",mon="rgba(20, 220, 220, 0.7)";var pd,ps,last_mode="E";function reloadContainer(t,e){let a=$(t);a.empty(),a.html(e)}function show_expiries(t){dd=document.getElementById(old_date),dd.style.display="none",dd=document.getElementById(t),dd.style.display="block",dd=document.getElementById("expiriesDropdown"),dd.click(),old_date=t}function highlight(t){var e=t.style.backgroundColor;t.style.backgroundColor="gray",setTimeout(function(){t.style.backgroundColor=e},1e3)}function update_timestamp(t,e,a){new_text=t+" $"+e+" Last updated: "+a+", NYSE time (15 minutes delayed)",label=document.getElementById("calltimestamp"),label.textContent=new_text,label=document.getElementById("puttimestamp"),label.textContent=new_text,label=document.getElementById("toptimestamp"),label.textContent=new_text}function update_portfolio(t,e,a,r,o){if(portfoliodiv=document.getElementById("portfoliodiv"),portfoliotext=document.getElementById("portfoliotext"),0===t.length)portfoliodiv.style.display="none",portfoliotext.style.display="flex";else{portfoliodiv.style.display="flex",portfoliotext.style.display="none",$("#portfoliotable tbody tr").remove(),tbodyRef=document.getElementById("portfoliotable").getElementsByTagName("tbody")[0];for(let a=0;a<t.length;a++)newRow=tbodyRef.insertRow(),newCell=newRow.insertCell(),newText=document.createTextNode(t[a]),newCell.appendChild(newText),newCell=newRow.insertCell(),newText=document.createTextNode(e[a]),newCell.appendChild(newText);exprtxt=document.getElementById("expr"),exprtxt.innerHTML=a,winptxt=document.getElementById("winp"),winptxt.innerHTML=r+"%",winptxt=document.getElementById("totcost"),winptxt.innerHTML=o,render_portfolio_charts(last_mode)}}function trim_sharpe(t){return t<-10?"-10+":t>10?"10+":t}function update_tables(){call_table=document.getElementById("calltable");for(let t=0;t<callchain.length;t++){for(let e=0;e<6;e++)cell=call_table.rows[t+1].cells[e+1],cell.innerHTML=callchain[t][e].toFixed(2);expected=call_table.rows[t+1].cells[7],expected.innerHTML=callchain[t][6].toFixed(2)+"%",sharpe=call_table.rows[t+1].cells[8],sharpe.innerHTML=trim_sharpe(callchain[t][7].toFixed(2)),callchain[t][6]>=0?(expected.style.color="green",sharpe.style.color="green"):(expected.style.color="red",sharpe.style.color="red")}put_table=document.getElementById("puttable");for(let t=0;t<putchain.length;t++){for(let e=0;e<6;e++)cell=put_table.rows[t+1].cells[e+1],cell.innerHTML=putchain[t][e].toFixed(2);expected=put_table.rows[t+1].cells[7],expected.innerHTML=putchain[t][6].toFixed(2)+"%",sharpe=put_table.rows[t+1].cells[8],sharpe.innerHTML=trim_sharpe(putchain[t][7].toFixed(2)),putchain[t][6]>=0?(expected.style.color="green",sharpe.style.color="green"):(expected.style.color="red",sharpe.style.color="red")}}function render_portfolio_charts(t){var e=20,a=20,r=30,o=50;chart_elem=document.getElementById("portfoliochartdiv"),width=chart_elem.offsetWidth-o-a,height=Math.max(chart_elem.offsetHeight,500)-e-r,last_mode=t,d3.select("#portfoliochartdiv").selectAll("*").remove();var l=d3.select("#portfoliochartdiv").append("svg").attr("width",width+o+a).attr("height",height+e+r).append("g").attr("transform","translate("+o+","+e+")"),n=d3.scaleLinear().range([0,width]).domain([d3.min(pd,function(t){return t.x}),d3.max(pd,function(t){return t.x})]);if("E"===t)var i=d3.scaleLinear().range([height,0]).domain([d3.min(pd,function(t){return t.e}),d3.max(pd,function(t){return t.e})]);else i=d3.scaleLinear().range([height,0]).domain([d3.min(pd,function(t){return t.pe}),d3.max(pd,function(t){return t.pe})]);l.append("g").attr("class","axis axis--x").attr("transform","translate(0,"+height+")").call(d3.axisBottom(n)).append("text").attr("x",width/2).attr("y",.9*r).attr("fill","#000").text("Price at expiration"),ylabel="E"===t?"Return":"Return * Probability",l.append("g").attr("class","axis axis--y").call(d3.axisLeft(i)).append("text").attr("transform","rotate(-90)").attr("x",-height/2+r).attr("y",.85*-o).attr("fill","#000").text(ylabel),l.append("path").datum(pd).attr("fill","none").attr("stroke",mon).attr("stroke-width",1.5).attr("d",d3.line().x(function(t){return n(t.x)}).y(function(e){return i("E"===t?e.e:e.pe)}));var d=d3.select("#portfoliochartdiv").append("div").style("opacity",0).attr("class","tooltip").style("background-color","white").style("border","solid").style("border-width","2px").style("border-radius","5px").style("padding","5px");l.append("g").selectAll("dot").data(ps).enter().append("circle").attr("class","myCircle").attr("cx",function(t){return n(t.x)}).attr("cy",function(e){return i("E"===t?e.e:e.pe)}).attr("r",6).attr("stroke",mon).attr("fill",mon).attr("stroke-width",3).on("mouseover",function(t){d.style("opacity",1)}).on("mousemove",function(t){d.html("Strike "+t.x+"<br>Return "+t.e).style("left",d3.mouse(this)[0]+70+"px").style("top",d3.mouse(this)[1]+"px")}).on("mouseleave",function(t){d.style("opacity",0)})}function render_rnd_charts(){var t={top:20,right:20,bottom:30,left:50};chart_elem=document.getElementById("chartdiv"),width=chart_elem.offsetWidth-t.left-t.right,height=Math.max(chart_elem.offsetHeight,500)-t.top-t.bottom,d3.select("#chartdiv").selectAll("*").remove();var e=d3.select("#chartdiv").append("svg").attr("width",width+t.left+t.right).attr("height",height+t.top+t.bottom),a=e.append("g").attr("transform","translate("+t.left+","+t.top+")"),r=d3.scaleLinear().range([0,width]).domain([d3.min(rnd_data,function(t){return t.x}),d3.max(rnd_data,function(t){return t.x})]),o=d3.scaleLinear().range([height,0]).domain([0,Math.max(d3.max(rnd_data,function(t){return t.y}),d3.max(rnd_modded,function(t){return t.y}))]),l=d3.area().curve(d3.curveMonotoneX).x(function(t){return r(t.x)}).y0(o(0)).y1(function(t){return o(t.y)});a.append("g").attr("class","axis axis--x").attr("transform","translate(0,"+height+")").call(d3.axisBottom(r)).append("text").attr("x",width/2).attr("y",.9*t.bottom).attr("fill","#000").text("Price at Expiration"),a.append("g").attr("class","axis axis--y").call(d3.axisLeft(o)).append("text").attr("transform","rotate(-90)").attr("x",-height/2+t.bottom).attr("y",.85*-t.left).attr("fill","#000").text("Probability"),p(rnd_data,"url(#svgGradient)"),p(rnd_modded,"url(#svgGradientMod)");const n=e.append("defs"),i=n.append("linearGradient").attr("id","svgGradient"),d=n.append("linearGradient").attr("id","svgGradientMod");s(i,bof,bon),s(d,mof,mon);const c=d3.bisector(t=>t.x).left;function p(r,o){a.selectAll(".area").data(r).enter().append("g").attr("d",l);e.append("path").datum(r).style("fill",o).attr("d",l).attr("transform","translate("+t.left+","+t.top+")").on("mouseover",y).on("mousemove",h).on("mouseout",x)}function s(t,e,a){t.append("stop").attr("class","start").attr("offset",grp).attr("stop-color",e),t.append("stop").attr("class","start").attr("offset",grp).attr("stop-color",a),t.append("stop").attr("class","end").attr("offset",grp).attr("stop-color",a).attr("stop-opacity",1),t.append("stop").attr("class","end").attr("offset",grp).attr("stop-color",e)}var u=d3.select("body").append("div").attr("class","tooltip").style("opacity",0),f=e.append("circle").style("opacity",0).attr("r",3).attr("stroke",bon).attr("fill",bon).attr("stroke-width",3),m=e.append("text").style("opacity",0).style("fill",bon);function y(t){u.style("opacity",1),f.style("opacity",1),m.style("opacity",1)}function h(e){const a=d3.mouse(this)[0],l=r.invert(a),n=c(e,l,1),i=e[0],d=e[n];subrndp=0,subrndmodp=0;for(let t=0;t<n;t++)subrndp+=parseFloat(rnd_data[t].c),subrndmodp+=parseFloat(rnd_modded[t].c);const p=r(i.x)/width*100,s=r(d.x)/width*100;d3.selectAll(".start").attr("offset",`${p}%`),d3.selectAll(".end").attr("offset",`${s}%`),f.attr("cx",r(d.x)+t.left).attr("cy",o(0)+t.top),m.attr("x",r(d.x)+t.left).attr("y",o(0)+t.top-10).style("font-size","15px").attr("alignment-baseline","middle").text(d.x.toFixed(2)),u.html("RND "+subrndp.toFixed(2)+"%<br>Predicted "+subrndmodp.toFixed(2)+"%").style("left",d3.event.pageX+20+"px").style("top",d3.event.pageY+"px").style("color","#273746")}function x(){u.style("opacity",0),f.style("opacity",0),m.style("opacity",0),d3.selectAll(".start").attr("offset",grp),d3.selectAll(".end").attr("offset",grp)}cx=70,cy1=30,cy2=60,e.append("circle").attr("cx",cx).attr("cy",cy1).attr("r",6).style("fill",bon),e.append("circle").attr("cx",cx).attr("cy",cy2).attr("r",6).style("fill",mon),e.append("text").attr("x",cx+20).attr("y",cy1+5).text("Risk Neutral distribution (RND)").style("font-size","15px").attr("alignment-baseline","middle"),e.append("text").attr("x",cx+20).attr("y",cy2+5).text("User adjusted RND").style("font-size","15px").attr("alignment-baseline","middle")}function getCookie(t){let e=null;if(document.cookie&&""!==document.cookie){const a=document.cookie.split(";");for(let r=0;r<a.length;r++){const o=a[r].trim();if(o.substring(0,t.length+1)===t+"="){e=decodeURIComponent(o.substring(t.length+1));break}}}return e}$(document).ready(function(){if(chart_elem=document.getElementById("chartdiv"),null===chart_elem)return;document.getElementById("portfoliodiv").style.display="none";const t=getCookie("csrftoken");var e=["mean_up","mean_down","var_up","var_down","reset"],a=["callinc","calldec","putinc","putdec"];update_tables(),$.ajaxSetup({beforeSend:function(e,a){var r;r=a.type,/^(GET|HEAD|OPTIONS|TRACE)$/.test(r)||this.crossDomain||e.setRequestHeader("X-CSRFToken",t)}}),$("button").click(function(t){var r=$(this).val();"sync"===r&&(t.preventDefault(),$.ajax({type:"POST",url:"sync",data:{ticker:ticker,expiry:expiry,callqty:callqty,putqty:putqty,mean_level:mean_level,var_level:var_level},success:function(t){callchain=t.callchain,putchain=t.putchain,price=t.price,rnd_data=t.chart,rnd_modded=t.chart_modded,render_rnd_charts(),update_tables(),update_timestamp(ticker,price,t.datetime),pd=t.portfoliochart,ps=t.strikes,portfolio_label=t.portfolio_label,portfolio_qty=t.portfolio_qty,expr=t.expr,winp=t.winp,totcost=t.totcost,chart=pd,strikes=ps,update_portfolio(portfolio_qty,portfolio_label,expr,winp,totcost)},error:function(t){console.log("Uh Oh. Options data sync error:",t)}})),"toggle"===r&&(t.preventDefault(),"E"===last_mode?(last_mode="PE",$(this).find("i").removeClass("fa-toggle-off").toggleClass("fa-toggle-on")):(last_mode="E",$(this).find("i").removeClass("fa-toggle-on").toggleClass("fa-toggle-off")),render_portfolio_charts(last_mode)),e.includes(r)&&(t.preventDefault(),"mean_up"===r?mean_level+=1:"mean_down"===r?mean_level-=1:"var_up"===r?var_level+=1:"var_down"===r?var_level-=1:"reset"===r&&(mean_level=0,var_level=0),$.ajax({type:"POST",url:"update_chart",data:{ticker:ticker,expiry:expiry,callchain:JSON.stringify(callchain),putchain:JSON.stringify(putchain),callqty:callqty,putqty:putqty,mean_level:mean_level,var_level:var_level,distrib_params:distrib_params},success:function(t){rnd_data=t.chart,rnd_modded=t.chart_modded,callchain=t.callchain,putchain=t.putchain,render_rnd_charts(),update_tables(),pd=t.portfoliochart,ps=t.strikes,portfolio_label=t.portfolio_label,portfolio_qty=t.portfolio_qty,expr=t.expr,winp=t.winp,totcost=t.totcost,chart=pd,strikes=ps,update_portfolio(portfolio_qty,portfolio_label,expr,winp,totcost)},error:function(t){console.log("Uh Oh. Chart update error:",t)}})),a.includes(r)&&(t.preventDefault(),index=$(this)[0].name,"callinc"===r||"calldec"===r?("callinc"===r?callqty[index]+=1:callqty[index]-=1,el=document.getElementById("c"+index),el.innerHTML=callqty[index]):"putinc"!==r&&"putdec"!==r||("putinc"===r?putqty[index]+=1:putqty[index]-=1,el=document.getElementById("p"+index),el.innerHTML=putqty[index]),$.ajax({type:"POST",url:"update_portfolio",data:{ticker:ticker,expiry:expiry,callchain:JSON.stringify(callchain),putchain:JSON.stringify(putchain),callqty:callqty,putqty:putqty,mean_level:mean_level,var_level:var_level,distrib_params:distrib_params},success:function(t){pd=t.portfoliochart,ps=t.strikes,portfolio_label=t.portfolio_label,portfolio_qty=t.portfolio_qty,expr=t.expr,winp=t.winp,totcost=t.totcost,update_portfolio(portfolio_qty,portfolio_label,expr,winp,totcost)},error:function(t){console.log("Uh Oh. Portfolio update error:",t)}}))}),render_rnd_charts()});
