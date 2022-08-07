var scale = 0.2,
  width = 800,
  height = 500,
  body = d3.select("#map-area"),
  classOrder = {
    'mlb': 1,
    'aaa': 2,
    'aax': 3,
    'afa': 4,
    'afx': 5,
    'asx': 6,
    'roa': 7,
    'rok': 8,
  },
  small,
  large,
  $modalTitle = $("#large-map .modal-title"),
  $modal = $("#large-map"),
  $prev = $("#large-map-prev"),
  $next = $("#large-map-next");

function setupGeo(scale) {
  var projection = d3.geo.albers()
      .rotate([96, 0])
      .center([-0.6, 38.7])
      .parallels([29.5, 45.5])
      .scale(scale * 1070)
      .translate([scale * width / 2, scale * height / 2])
      .precision(0.1),
    path = d3.geo.path()
      .projection(projection);
  return { projection: projection, path: path };
}

function getRect(el) {
  var bbox = el.getBBox(),
    pos = d3.transform(el.parentNode.getAttribute("transform")).translate;
  return {
    x1: pos[0] + bbox.x,
    x2: pos[0] + bbox.x + bbox.width,
    y1: pos[1] + bbox.y,
    y2: pos[1] + bbox.y + bbox.height
  };
}

small = setupGeo(scale);
large = setupGeo(1);

queue()
  .defer(d3.json, "data/north_am_topo.json")
  .defer(d3.csv, "data/teams.csv")
  .defer(d3.csv, "data/colors.csv")
  .await(function (error, na, teams, colors) {
    var lg_svg, container, svg, team, largeMapDisplay;

    if (error) { return console.error(error); }

    colors = d3.nest()
      .key(function (d) { return d.team_id; })
      .map(colors, d3.map);

    teams = teams.filter(function (d) { return d.affiliate_id !== "11"; });

    teams = d3.nest()
      .key(function (d) { return d.affiliate_id; })
      .entries(teams);

    teams.forEach(function (d) {
      var coords,
        primary = d3.hsl(colors.get(d.key)[0].primary),
        secondary = "#909090",
        team_colors = d3.scale.linear()
          .domain([1, 7])
          .range([primary, secondary])
          .interpolate(d3.interpolateHcl);

      d.values.sort(function (a, b) {
        return classOrder[b.level] - classOrder[a.level];
      });
      coords = d.values.map(function (v) {
        return [v.longitude, v.latitude];
      });
      d.values.forEach(function (d) {
        d.color = team_colors(classOrder[d.level]);
      });
      d.route = { type: "LineString", coordinates: coords, color: primary };
      d.center = d3.geo.centroid(d.route);
      d.routeDist = d3.geo.length(d.route);
      d.majTeamName = d.values[d.values.length - 1].team;
    });

    teams.sort(function (a, b) {
      return a.routeDist - b.routeDist;
    });
    
    largeMapDisplay = function (d, i) {
      var route, totalLength, team, teamEnter, teamNames, animationTime,
        routeSpeed = 3.3,
        delayTime = 400,
        transitionTime = 500,
        modalIsOpen = $modal.data('bs.modal') && $modal.data('bs.modal').isShown;

      function labelOffset(p) {
        var dist = 7;
        if (p.longitude < -115) {
          return dist;
        } else if (p.longitude > -80) {
          return -1 * dist;
        } else if (p.longitude < d.center[0]) {
          return -1 * dist;
        } else {
          return dist;
        }
      }

      route = lg_svg.selectAll(".route")
        .data([d], function (d) { return d.key; });
      route.enter().append("path")
        .datum(function (d) { return d.route; })
        .attr("class", "route")
        .attr("d", large.path)
        .style("stroke", function (d) { return d.color; });
      if (modalIsOpen) {
        route.exit().transition()
          .duration(transitionTime)
          .style("opacity", 1e-6)
          .remove();
      } else {
        route.exit().remove();
      }
      totalLength = route.node().getTotalLength();
      route.attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength);

      team = lg_svg.selectAll(".team")
        .data(d.values, function (d) { return d.team_id; });
      teamEnter = team.enter().append("g")
        .attr("class", "team")
        .attr("transform", function (d) {
          return "translate(" + large.projection([d.longitude, d.latitude]) + ")";
        });
      teamEnter.append("circle")
        .attr("r", 1e-6)
        .style("fill", function (d) { return d.color; })
        .transition()
        .duration(transitionTime)
        .attr("r", 4);
      teamNames = teamEnter.append("text")
        .attr("x", labelOffset)
        .attr("y", 0)
        .attr("dy", "0.35em")
        .style("opacity", 0)
        .attr("text-anchor", function (d) {
          return labelOffset(d) > 0 ? "start" : "end";
        })
        .text(function (d) { return d.team + " (" + d.level_display + ")"; });
      if (modalIsOpen) {
        team.exit().selectAll("circle").transition()
          .duration(transitionTime)
          .attr("r", 1e-6)
          .remove();
        team.exit().selectAll("text").transition()
          .duration(transitionTime)
          .style("opacity", 1e-6)
          .each('end', function () { d3.select(this.parentNode).remove(); });
      } else {
        team.exit().remove();
      }
      
      function doAnimate() {
        // jiggle the labels so that they don't overlap
        var stop = false,
          iter = 0,
          max = 20,
          step = 0.5;
        
        // flip it around if it's going over the right edge
        d3.selectAll("text").each(function (a) {
          var text, rect = getRect(this);
          if (rect.x2 > width) {
            text = d3.select(this);
            text.attr("x", -1 * text.attr("x"));
            text.attr("text-anchor", text.attr("text-anchor") === "start" ?
                      "end" : "start");
          }
        });
        
        //  bump labels up or down if colliding 
        while (!stop && iter < max) {
          stop = true;
          iter += 1;
          d3.selectAll("text").each(function (a, ia) {
            var aRect = getRect(this),
              aText = d3.select(this);
            d3.selectAll("text").each(function (b, ib) {
              if (ia === ib) { return; }
              var bRect = getRect(this),
                bText = d3.select(this);
              if (aRect.x1 < bRect.x2 && aRect.x2 > bRect.x1 &&
                  aRect.y1 < bRect.y2 && aRect.y2 > bRect.y1) {
                stop = false;
                if (aRect.y1 < bRect.y1) {
                  aText.attr("y", parseFloat(aText.attr("y")) - step);
                  bText.attr("y", parseFloat(bText.attr("y")) + step);
                } else {
                  aText.attr("y", parseFloat(aText.attr("y")) + step);
                  bText.attr("y", parseFloat(bText.attr("y")) - step);
                }
              }
            });
          });
        }

        // draw the route and fade in the team names
        animationTime = routeSpeed * totalLength;
        route.transition()
          .delay(delayTime)
          .duration(animationTime)
          .ease("linear")
          .attr("stroke-dashoffset", 0);
        teamNames.transition()
          .delay(delayTime + animationTime)
          .duration(200)
          .style("opacity", 1);
      }
      
      $modalTitle.fadeOut({
        done: function () {
          $modalTitle.css("background-image", "url(img/" + d.key + ".png)");
          $modalTitle.text(d.majTeamName);
          $modalTitle.fadeIn();
        }
      });
      
      if (modalIsOpen) {
        doAnimate();
      } else {
        $modal.modal();
        $modal.on("shown.bs.modal", doAnimate);
        $modal.on("hidden.bs.modal", function (e) {
          teamNames.style("opacity", 0);
        });
      }
      if (i > 0) {
        $prev.show();
        $prev.unbind('click').click(function (evt) {
          evt.preventDefault();
          largeMapDisplay(teams[i - 1], i - 1);
        });
      } else {
        $prev.hide();
      }
      if (i < teams.length - 1) {
        $next.show();
        $next.unbind('click').click(function (evt) {
          evt.preventDefault();
          largeMapDisplay(teams[i + 1], i + 1);
        });
      } else {
        $next.hide();
      }
    };

    lg_svg = d3.select("#large-map-target")
      .append("svg")
      .attr("width", width)
      .attr("height", height);
    lg_svg.append("path")
      .datum(topojson.feature(na, na.objects.north_am))
      .attr("d", large.path)
      .attr("class", "land");
    lg_svg.append("path")
      .datum(topojson.mesh(na, na.objects.north_am, function (a, b) {
        return a.properties.name !== b.properties.name;
      }))
      .attr("d", large.path)
      .attr("class", "state-boundary");

    container = body.selectAll(".map-container")
      .data(teams)
      .enter().append("div")
      .attr("class", "map-container")
      .on("click", largeMapDisplay);

    container.append("p")
      .text(function (d) { return d.majTeamName; });

    svg = container.append("svg")
      .attr("width", scale * width)
      .attr("height", scale * height);

    // north america landmass
    svg.append("path")
      .datum(topojson.feature(na, na.objects.north_am))
      .attr("d", small.path)
      .attr("class", "land");

    // path between points
    svg.append("path")
      .datum(function (d) { return d.route; })
      .attr("class", "route")
      .attr("d", small.path)
      .style("stroke", function (d) { return d.color; });

    // city points
    team = svg.selectAll(".team")
      .data(function (d) { return d.values; });
    team.enter().append("g")
      .attr("class", "team")
      .attr("transform", function (d) {
        return "translate(" + small.projection([d.longitude, d.latitude]) + ")";
      });
    team.append("circle")
      .attr("r", 2)
      .style("fill", function (d) {
        return d.color;
      });
    team.exit().remove();
  });

$(function () {
  var headerHeight = $(".jumbotron").outerHeight();
  
  function parallax() {
    var scrolled = $(window).scrollTop();
    $(".bg").css("height", (headerHeight - scrolled) + "px");
  }

  $(window).scroll(parallax);
});