function drawRaster(parent_id, data, trial_events, event_types)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50},
        width = scaleFactor*(960 - margin.left - margin.right),
        height = scaleFactor*(250 - margin.top - margin.bottom);

    var raster_svg = d3.select('#'+parent_id).append('svg:svg')
        .attr('width', width + margin.right + margin.left)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var align_event = d3.select("#align_event").node().value;
    d3.selectAll("#align_event").on("change.raster."+parent_id, update);
    var realigned_data=realign_spikes(data, trial_events, align_event);
    var realigned_trial_events=realign_events(trial_events, align_event);

    var xScale = d3.scale.linear()
        .range([0, width]);

    var yScale = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom").ticks(5);

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left").ticks(5);

    // Scale the range of the data
    xScale.domain([d3.min(realigned_data, function(d) { return d.x; }), d3.max(realigned_data, function(d) { return d.x; })]);
    yScale.domain([0, d3.max(realigned_data, function(d) { return d.y; })]);

    var raster=raster_svg.append("g")
        .attr("class", "raster");

    raster.selectAll("circle")
        .data(realigned_data)
        .enter().append("svg:circle")
        .attr("transform", function (d) { return "translate("+xScale(d.x)+", "+yScale(d.y)+")"})
        .attr("r", 1);

    var events = raster_svg.append("g")
        .attr("class","events");

    var event_circles=events.selectAll("circle")
        .data(realigned_trial_events)
        .enter().append("svg:circle")
        .attr("transform", function (d) { return "translate("+xScale(d.t)+", "+yScale(d.trial)+")"})
        .attr("r", 4)
        .style('fill', function (d) {return p(event_types.indexOf(d.name))})
        .on("mouseover", function(d) {
            focus.attr("transform", "translate(" + xScale(d.t) + "," + yScale(d.trial) + ")");
            focus.select("text").text(d.name);
            focus.style("display","")
        })
        .on("click", function(d) {
            align_all_events(d.name);
        });

    var focus = raster_svg.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 6);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".5em");

    raster_svg.append("svg:g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    raster_svg.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    raster_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    raster_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Trial");

    function update()
    {
        var align_event = d3.select("#align_event").node().value;

        focus.style("display","none");
        realigned_data=realign_spikes(data, trial_events, align_event);
        realigned_trial_events=realign_events(trial_events, align_event);

        xScale.domain([d3.min(realigned_data, function(d) { return d.x; }), d3.max(realigned_data, function(d) { return d.x; })]);
        xAxis.scale(xScale);

        raster_svg.selectAll("circle")
            .data(realigned_data)
            .attr("transform", function (d) { return "translate("+xScale(d.x)+", "+yScale(d.y)+")"});

        events.selectAll("circle")
            .data(realigned_trial_events)
            .attr("transform", function (d) { return "translate("+xScale(d.t)+", "+yScale(d.trial)+")"})

        raster_svg.selectAll(".text").data(hist).remove();
        raster_svg.select(".x.axis").call(xAxis);
    }
}