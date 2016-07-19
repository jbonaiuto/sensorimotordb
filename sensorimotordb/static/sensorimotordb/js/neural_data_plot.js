var bisectTime = d3.bisector(function(d) { return d.x; }).left;
var p=d3.scale.category10();

var dispatch=d3.dispatch("statechange","realigned");

function drawPieChart(classifications, parent_id, on_click)
{
    $('#'+parent_id).empty();

    var pie = new d3pie(parent_id, {
        "footer": {
            "color": "#999999",
            "fontSize": 10,
            "font": "open sans",
            "location": "bottom-left"
        },
        "size": {
            "canvasWidth": 590,
            "pieOuterRadius": "90%"
        },
        "data": {
            "sortOrder": "value-desc",
            "content": classifications
        },
        "labels": {
            "outer": {
                "pieDistance": 32
            },
            "inner": {
                "hideWhenLessThanPercentage": 3
            },
            "mainLabel": {
                "fontSize": 11
            },
            "percentage": {
                "color": "#ffffff",
                "decimalPlaces": 0
            },
            "value": {
                "color": "#adadad",
                "fontSize": 11
            },
            "lines": {
                "enabled": true
            },
            "truncation": {
                "enabled": true
            }
        },
        "effects": {
            "pullOutSegmentOnClick": {
                "effect": "linear",
                "speed": 400,
                "size": 8
            }
        },
        "misc": {
            "gradient": {
                "enabled": true,
                "percentage": 100
            }
        },
        callbacks: {
            onClickSegment: on_click
        }
    });
}

function drawRaster(id, parent_id, trial_spikes, trial_events, event_types)
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
    xScale.domain([d3.min([d3.min(trial_events,function(d){return d.t}),d3.min(trial_spikes,function(d){return d.x})]),
        d3.max([d3.max(trial_events,function(d){return d.t}),d3.max(trial_spikes,function(d){return d.x})])]);
    yScale.domain([d3.min(trial_spikes, function(d) { return d.y; }), d3.max(trial_spikes, function(d) { return d.y; })]);

    var raster=raster_svg.append("g")
        .attr("class", "raster");

    raster.selectAll("circle")
        .data(trial_spikes)
        .enter().append("svg:circle")
        .attr("transform", function (d) { return "translate("+xScale(d.x)+", "+yScale(d.y)+")"})
        .attr("r", 1);

    var events = raster_svg.append("g")
        .attr("class","events");

    var event_circles=events.selectAll("circle")
        .data(trial_events)
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
            d3.select("#align_event").node().value= d.name;
            dispatch.statechange();
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

    dispatch.on("realigned.raster."+parent_id, update);
    function update(realigned_data, realigned_trial_events)
    {
        var data=realigned_data.get(id);
        var trial_events=realigned_trial_events.get(id);
        focus.style("display","none");

        xScale.domain([d3.min(data, function(d) { return d.x; }),d3.max(data, function(d) { return d.x; })]);
        xAxis.scale(xScale);

        raster_svg.selectAll("circle")
            .data(data)
            .attr("transform", function (d) { return "translate("+xScale(d.x)+", "+yScale(d.y)+")"});

        events.selectAll("circle")
            .data(trial_events)
            .attr("transform", function (d) { return "translate("+xScale(d.t)+", "+yScale(d.trial)+")"})

        raster_svg.selectAll(".text").data(hist).remove();
        raster_svg.select(".x.axis").call(xAxis);
    }
}

function drawHistogram(id, parent_id, data, trial_events, event_types)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scaleFactor*(960 - margin.left - margin.right)
        , height = scaleFactor*(200 - margin.top - margin.bottom);

    var histo_svg = d3.select('#'+parent_id).append('svg:svg')
        .attr('width', width + margin.right + margin.left)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var binwidth = parseInt(d3.select("#binwidth").node().value);

    var timeMin=d3.min([d3.min(trial_events,function(d){return d.t}),d3.min(data,function(d){return d.x})]);
    var timeMax=d3.max([d3.max(trial_events,function(d){return d.t}),d3.max(data,function(d){return d.x})]);

    var xScale = d3.scale.linear()
        .range([0, width])
        .domain([timeMin, timeMax]);

    var yScale = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom").ticks(5);

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left").ticks(5);

    var numTrials=d3.max(data, function(d){ return d.y});

    hist = d3.layout.histogram()
        .bins(d3.range(xScale.domain()[0], xScale.domain()[1]+binwidth, binwidth))
        (data.map(function(d) {return d.x; }));

    var scaledHist=[];
    for(var j=0; j<hist.length; j++)
        scaledHist.push({
            x: hist[j].x,
            y: hist[j].y/numTrials/(binwidth/1000.0)
        });

    var xBinwidth = width / (scaledHist.length -1);
    var yMax=d3.max(scaledHist, function(d) { return d.y+1; });
    yScale.domain([0, yMax +.1*yMax])

    histo_svg.selectAll(".histo-bar")
        .data(scaledHist)
        .enter().append("rect")
        .attr("class", "histo-bar")
        .attr("width", function(d) { return xBinwidth })
        .attr("height", function(d) { return d3.max([0,height- yScale(d.y)-1]); })
        .attr("x", function(d) {return xScale(d.x)})
        .attr("y", function(d) {return yScale(d.y)});

    histo_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    histo_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_notes=[];
    var event_lines=[];
    var event_areas=[];
    for(var i=0; i<event_types.length; i++)
    {
        var event_type=event_types[i];
        var times=[];
        for(var j=0; j<trial_events.length; j++)
        {
            if(trial_events[j].name==event_type)
                times.push(trial_events[j].t);
        }
        if(times.length>0)
        {
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_lines.push(
                histo_svg.append("line")
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(0))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
            );
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_areas.push(
                histo_svg.append("line")
                    .attr("x1", area_x)
                    .attr("y1", yScale(0))
                    .attr("x2", area_x)
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
                    .style("stroke", p(i))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
            );
            var event_note=
                event_notes.push(
                    histo_svg.selectAll(".g-note")
                        .data([event_type])
                        .enter().append("text")
                        .classed("annotation-text",true)
                        .style('fill', p(i))
                        .attr("x", xScale(mean_time))
                        .attr("y", yScale(yMax +.1*yMax))
                        .attr("dy", function(d, i) { return i * 1.3 + "em"; })
                        .text(function(d) { return d; })
                        .on("click", function(d) {
                            d3.select("#align_event").node().value= d;
                            dispatch.statechange();
                        })
                );
        }
    }


    // draw the x axis
    histo_svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    // draw the x axis
    histo_svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    var old_binwidth = binwidth;
    var old_xBinwidth = xBinwidth;
    dispatch.on("realigned.histo."+parent_id, update);
    function update(realigned_data, realigned_trial_events) {
        var data=realigned_data.get(id);
        var trial_events=realigned_trial_events.get(id);

        binwidth = parseInt(d3.select("#binwidth").node().value);

        xScale.domain([d3.min(data, function(d) { return d.x; }), d3.max(data, function(d) { return d.x; })]);

        hist = d3.layout.histogram()
            .bins(d3.range(xScale.domain()[0], xScale.domain()[1]+binwidth, binwidth))
            (data.map(function(d) {return d.x; }));

        scaledHist=[];
        for(var j=0; j<hist.length; j++)
            scaledHist.push({
                x: hist[j].x,
                y: hist[j].y/numTrials/(binwidth/1000.0)
            });

        xAxis.scale(xScale);
        var yMax=d3.max(scaledHist, function(d) { return d.y+1; });
        yScale.domain([0, yMax +.1*yMax]);
        xBinwidth =  width / (scaledHist.length-1);

        var xEase = "cubic-in-out";
        var yEase = "bounce";

        histo_svg.selectAll(".histo-bar").data(scaledHist)
            .enter().append("rect")
            .attr("class", "histo-bar")
            .attr("fill", "white")
            .attr("height", function(d) { return height- yScale(d.y)-1; })
            .attr("width", function(d) { return old_xBinwidth; })
            .attr("x", function(d) {return xScale(d.x) * old_binwidth / binwidth})
            .attr("y", function(d) {return yScale(d.y)});

        histo_svg.selectAll(".histo-bar").data(scaledHist)
            .transition().duration(1000).ease(yEase)
            .attr("y", function(d) {return yScale(d.y)})
            .attr("height", function(d) { return height- yScale(d.y)-1; })
            .attr("fill", function (d) {return "hsl(" + (1-(d.y-yScale.domain()[0])/(yScale.domain()[1]-yScale.domain()[0]))*255 + ", 85%, 75%)"})
            .transition().duration(1000).ease(xEase)
            .attr("x", function(d) {return xScale(d.x)})
            .attr("width", function(d) { return xBinwidth; });

        histo_svg.selectAll(".histo-bar").data(scaledHist).exit()
            .transition().duration(1000).ease(yEase)
            .attr("y", function(d) {return yScale(d.y)})
            .attr("height", function(d) { return height- yScale(d.y)-1; })
            .transition().duration(1000).ease(xEase)
            .attr("width", function(d) { return xBinwidth; })
            .attr("x", function(d) {return xScale(d.x) * binwidth / old_binwidth})
            .remove();

        for(var i=0; i<event_types.length; i++)
        {
            var times=[];
            for(var j=0; j<trial_events.length; j++)
            {
                if(trial_events[j].name==event_types[i])
                    times.push(trial_events[j].t);
            }
            if(times.length>0)
            {
                var mean_time=d3.mean(times);
                var min_time=d3.min(times);
                var max_time=d3.max(times);
                event_lines[i]
                    .attr("x1", xScale(mean_time))
                    .attr("x2",xScale(mean_time));
                var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
                event_areas[i]
                    .attr("x1", area_x)
                    .attr("x2", area_x)
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                event_notes[i].attr("x", xScale(mean_time))
            }
        }
        histo_svg.selectAll(".text").data(hist).remove();

        histo_svg.select(".y.axis").call(yAxis);
        histo_svg.select(".x.axis").call(xAxis);

        old_binwidth = binwidth;
        old_xBinwidth = xBinwidth;

    }
}

function drawFiringRate(id, parent_id, data, trial_events, event_types)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scaleFactor*(960 - margin.left - margin.right)
        , height = scaleFactor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#"+parent_id).append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var binwidth = parseInt(d3.select("#binwidth").node().value);
    var kernelwidth = parseInt(d3.select("#kernelwidth").node().value);

    var rate=get_firing_rate(data, binwidth, kernelwidth);

    var timeMin=d3.min([d3.min(trial_events,function(d){return d.t}),d3.min(rate,function(d){return d.x})]);
    var timeMax=d3.max([d3.max(trial_events,function(d){return d.t}),d3.max(rate,function(d){return d.x})]);
    var xScale = d3.scale.linear()
        .range([0, width])
        .domain([timeMin, timeMax]);

    var yScale = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left");

    var line = d3.svg.line()
        .x(function(d) { return xScale(d.x); })
        .y(function(d) { return yScale(d.y); });


    var yMax=d3.max(rate, function(d) { return d.y+1; });
    yScale.domain([0, yMax +.1*yMax])

    rate_svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    rate_svg.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    rate_svg.append("path")
        .datum(rate)
        .attr("class", "data-line")
        .attr("d", line);

    rate_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    rate_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_notes=[];
    var event_lines=[];
    var event_areas=[];
    for(var i=0; i<event_types.length; i++)
    {
        var event_type=event_types[i];
        var times=[];
        for(var j=0; j<trial_events.length; j++)
        {
            if(trial_events[j].name==event_type)
                times.push(trial_events[j].t);
        }
        if(times.length>0)
        {
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_lines.push(
                rate_svg.append("line")
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(0))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
            );
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_areas.push(
                rate_svg.append("line")
                    .attr("x1", area_x)
                    .attr("y1", yScale(0))
                    .attr("x2", area_x)
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
                    .style("stroke", p(i))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
            );
            event_notes.push(
                rate_svg.selectAll(".g-note")
                    .data([event_type])
                    .enter().append("text")
                    .classed("annotation-text",true)
                    .style('fill', p(i))
                    .attr("x", xScale(mean_time))
                    .attr("y", yScale(yMax +.1*yMax))
                    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
                    .text(function(d) { return d; })
                    .on("click", function(d) {
                        d3.select("#align_event").node().value= d;
                        dispatch.statechange();
                    })
            );
        }
    }

    var focus = rate_svg.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 4.5);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".35em");

    rate_svg.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    function mousemove() {
        var x0 = xScale.invert(d3.mouse(this)[0]),
            i = bisectTime(rate, x0, 1),
            d0 = rate[i - 1],
            d1 = rate[i],
            d = x0 - d0.x > d1.x - x0 ? d1 : d0;
        focus.attr("transform", "translate(" + xScale(d.x) + "," + yScale(d.y) + ")");
        focus.select("text").text(d.y.toFixed(2)+'Hz');
    }

    dispatch.on("realigned.rate."+parent_id, update);
    function update(realigned_data, realigned_trial_events){
        var data=realigned_data.get(id);
        var trial_events=realigned_trial_events.get(id);

        binwidth = parseInt(d3.select("#binwidth").node().value);
        kernelwidth = parseInt(d3.select("#kernelwidth").node().value);

        rate=get_firing_rate(data, binwidth, kernelwidth);

        var yMax=d3.max(rate, function(d) { return d.y+1; });
        yScale.domain([0, yMax +.1*yMax])
        yAxis.scale(yScale);
        xScale.domain([d3.min(rate, function(d) { return d.x; }), d3.max(rate, function(d) { return d.x; })]);
        xAxis.scale(xScale);

        xBinwidth =  width / (rate.length-1);

        for(var i=0; i<event_types.length; i++)
        {
            var times=[];
            for(var j=0; j<trial_events.length; j++)
            {
                if(trial_events[j].name==event_types[i])
                    times.push(trial_events[j].t);
            }
            if(times.length>0)
            {
                var mean_time=d3.mean(times);
                var min_time=d3.min(times);
                var max_time=d3.max(times);
                event_lines[i]
                    .attr("x1", xScale(mean_time))
                    .attr("x2",xScale(mean_time));
                var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
                event_areas[i]
                    .attr("x1", area_x)
                    .attr("x2", area_x)
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                event_notes[i].attr("x", xScale(mean_time))
            }
        }

        rate_svg.selectAll('.data-line').datum(rate)
            .transition().duration(1000)
            .attr("class", "data-line")
            .attr("d", line);

        rate_svg.selectAll(".text").data(hist).remove();
        rate_svg.select(".y.axis").call(yAxis);
        rate_svg.select(".x.axis").call(xAxis);

    }
}

function drawPopulationFiringRate(parent_id, legend_id, group_trials, group_trial_events, event_types, group_ids, group_names, scale_factor)
{
    var margin = {top: 30, right: 0, bottom: 40, left: 50}
        , width = scale_factor*(700 - margin.left - margin.right)
        , height = scale_factor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#"+parent_id)
        .append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var binwidth = parseInt(d3.select("#binwidth").node().value);
    var kernelwidth = parseInt(d3.select("#kernelwidth").node().value);
    var min_time=10000;
    var max_time=-10000;
    var max_rate=0;
    var rate_data=new Map();
    for(var i=0; i<group_ids.length; i++)
    {
        var group_id=group_ids[i];
        var rate=get_firing_rate(group_trials.get(group_id), binwidth, kernelwidth);
        rate_data.set(group_id,rate);
        var group_min_time=d3.min(rate, function(d){ return d.x; });
        var group_max_time=d3.max(rate, function(d){ return d.x; });
        if(group_min_time<min_time)
            min_time=group_min_time;
        if(group_max_time>max_time)
            max_time=group_max_time;
        var group_max_rate=d3.max(rate, function(d){ return d.y+1 });
        if(group_max_rate>max_rate)
            max_rate=group_max_rate;
    }

    var xScale = d3.scale.linear()
        .range([0, width])
        .domain([min_time, max_time]);

    var yScale = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left");

    var line = d3.svg.line()
        .x(function(d) { return xScale(d.x); })
        .y(function(d) { return yScale(d.y); });


    yScale.domain([0, max_rate +.1*max_rate]);

    rate_svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    rate_svg.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    var max_length=d3.max(group_names, function(d){return d.length});
    $('#'+legend_id).height(scale_factor*(400 - margin.bottom));

    var legend_svg = d3.select('#'+legend_id)
        .append("svg")
        .attr("width", 40+max_length*7)
        .attr("height", 20*(group_ids.length+1));

    var legend = legend_svg.append("g")
        .attr("class", "legend1")
        .attr('transform', 'translate(-20,50)');

    for(var i=0; i<group_ids.length; i++)
    {
        rate_svg.append("path")
            .attr("id", parent_id+"-group-"+group_ids[i])
            .datum(rate_data.get(group_ids[i]))
            .attr("class", "data-line")
            .style("stroke", p(i))
            .attr("d", line);
        legend.append("text")
            .attr("id",parent_id+"-label-group-"+group_ids[i])
            .attr("group_id",group_ids[i])
            .attr("class","legend-label")
            .attr("x", 40)
            .attr("y", (i-1) *  20 + 5)
            .style("fill", p(i))
            .text(group_names[i])
            .on("click", function(d) {
                var group_id=this.attributes['group_id'].value;
                var active=d3.select("#"+parent_id+"-group-"+group_id).attr("active")=="true" ? false : true,
                    newOpacity = active ? 0 : 1,
                    newLabelOpacity = active ? 0.25 : 1;
                d3.select("#"+parent_id+"-label-group-"+group_id).style("opacity",newLabelOpacity);
                d3.select("#"+parent_id+"-group-"+group_id).style("opacity",newOpacity);
                d3.select("#"+parent_id+"-group-"+group_id).attr("active",active);
            });
    }

    rate_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    rate_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_notes=[];
    var event_lines=[];
    var event_areas=[];
    for(var i=0; i<event_types.length; i++)
    {
        var event_type=event_types[i];
        var times=[];
        for(var k=0; k<group_ids.length; k++)
        {
            var group_id=group_ids[k];
            var group_times=[];
            var realigned_trial_events=group_trial_events.get(group_id)
            for(var j=0; j<realigned_trial_events.length; j++)
            {
                if(realigned_trial_events[j].name==event_type)
                    group_times.push(realigned_trial_events[j].t);
            }
            if(group_times.length>0)
                times.push(d3.mean(group_times));
        }
        if(times.length>0)
        {
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_lines.push(
                rate_svg.append("line")
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(0))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(max_rate +.1*max_rate))
                    .classed("annotation-line",true)
            );
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_areas.push(
                rate_svg.append("line")
                    .attr("x1", area_x)
                    .attr("y1", yScale(0))
                    .attr("x2", area_x)
                    .attr("y2", yScale(max_rate +.1*max_rate))
                    .classed("annotation-line",true)
                    .style("stroke", p(i))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
            );
            event_notes.push(
                rate_svg.selectAll(".g-note")
                    .data([event_type])
                    .enter().append("text")
                    .classed("annotation-text",true)
                    .style('fill', p(i))
                    .attr("x", xScale(mean_time))
                    .attr("y", yScale(max_rate +.1*max_rate))
                    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
                    .text(function(d) { return d; })
                    .on("click", function(d) {
                        d3.select("#align_event").node().value= d;
                        dispatch.statechange();
                    })
            );
        }
    }

    var focus = rate_svg.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 4.5);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".35em");

    rate_svg.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    function mousemove() {
        var x0 = xScale.invert(d3.mouse(this)[0]);
        var y0 = yScale.invert(d3.mouse(this)[1]);
        min_y_dist=10000;
        min_y_d=null;
        for(var j=0; j<group_ids.length; j++)
        {
            rate=rate_data.get(group_ids[j]);
            var i = bisectTime(rate, x0, 1);
            d0 = rate[i - 1];
            d1 = rate[i];
            d = x0 - d0.x > d1.x - x0 ? d1 : d0;
            y_dist=Math.abs(d.y-y0);
            if(y_dist<min_y_dist)
            {
                min_y_dist=y_dist;
                min_y_d=d;
            }
        }
        focus.attr("transform", "translate(" + xScale(min_y_d.x) + "," + yScale(min_y_d.y) + ")");
        focus.select("text").text(min_y_d.y.toFixed(2)+'Hz');
    }

    rate_svg.update=function update(realigned_data, realigned_trial_events){
        binwidth = parseInt(d3.select("#binwidth").node().value);
        kernelwidth = parseInt(d3.select("#kernelwidth").node().value);
        rate_data=new Map();
        var min_time=10000;
        var max_time=-10000;
        var max_rate=0;
        for(var i=0; i<group_ids.length; i++)
        {
            var group_id=group_ids[i];
            var rate=get_firing_rate(realigned_data.get(group_id), binwidth, kernelwidth);
            var group_min_time=d3.min(rate, function(d){ return d.x; });
            var group_max_time=d3.max(rate, function(d){ return d.x; });
            if(group_min_time<min_time)
                min_time=group_min_time;
            if(group_max_time>max_time)
                max_time=group_max_time;
            var group_max_rate=d3.max(rate, function(d){ return d.y+ 1 });
            if(group_max_rate>max_rate)
                max_rate=group_max_rate;
            rate_data.set(group_id, rate);

        }

        yScale.domain([0, max_rate +.1*max_rate]);
        yAxis.scale(yScale);
        xScale.domain([min_time, max_time]);
        xAxis.scale(xScale);

        xBinwidth =  width / (rate.length-1)
        for(var i=0; i<event_types.length; i++)
        {
            var event_type=event_types[i];
            var times=[];
            for(var k=0; k<group_ids.length; k++)
            {
                var group_id=group_ids[k];
                var group_times=[];
                var trial_events=realigned_trial_events.get(group_id);
                for(var j=0; j<trial_events.length; j++)
                {
                    if(trial_events[j].name==event_type)
                        group_times.push(trial_events[j].t);
                }
                if(group_times.length>0)
                    times.push(d3.mean(group_times));
            }
            if(times.length>0)
            {
                var mean_time=d3.mean(times);
                var min_time=d3.min(times);
                var max_time=d3.max(times);
                event_lines[i]
                    .attr("x1", xScale(mean_time))
                    .attr("x2",xScale(mean_time));
                var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
                event_areas[i]
                    .attr("x1", area_x)
                    .attr("x2", area_x)
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                event_notes[i].attr("x", xScale(mean_time))
            }
        }

        for(var i=0; i<group_ids.length; i++)
        {
            var group_id=group_ids[i];
            rate_svg.selectAll('#'+parent_id+'-group-'+group_id).datum(rate_data.get(group_id))
                .transition().duration(1000)
                .attr("class", "data-line")
                .attr("d", line);
        }
        rate_svg.selectAll(".text").data(hist).remove();
        rate_svg.select(".y.axis").call(yAxis);
        rate_svg.select(".x.axis").call(xAxis);

    }
    dispatch.on("realigned.rate.population."+parent_id, rate_svg.update);
    return rate_svg;
}

function drawMeanFiringRates(parent_id, group_mean_rates, group_trial_events, event_types, group_ids, group_names, scale_factor)
{
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scale_factor*(960 - margin.left - margin.right)
        , height = scale_factor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#"+parent_id).append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var min_time=10000;
    var max_time=-10000;
    var max_rate=0;
    var mean_rates=group_mean_rates;
    for(var i=0; i<group_ids.length; i++)
    {
        var group_id=group_ids[i];
        var rate=mean_rates.get(group_id);
        var group_min_time=d3.min(rate, function(d){ return d.x; });
        var group_max_time=d3.max(rate, function(d){ return d.x; });
        if(group_min_time<min_time)
            min_time=group_min_time;
        if(group_max_time>max_time)
            max_time=group_max_time;
        var group_max_rate=d3.max(rate, function(d){ return d.y+ d.stderr });
        if(group_max_rate>max_rate)
            max_rate=group_max_rate;
    }

    var xScale = d3.scale.linear()
        .range([0, width])
        .domain([min_time, max_time]);

    var yScale = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left");

    var line = d3.svg.line()
        .x(function(d) { return xScale(d.x); })
        .y(function(d) { return yScale(d.y); });

    yScale.domain([0, max_rate +.1*max_rate]);

    rate_svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    rate_svg.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    var max_length=d3.max(group_names, function(d){return d.length});

    for(var group_idx=0; group_idx<group_ids.length; group_idx++)
    {
        var mean_rate=mean_rates.get(group_ids[group_idx]);

        // Define a convenience function to calculate the
        // path for a slice of the data.
        var slice = function(d,i) {
            var x = i ? mean_rate[i-1].x : d.x,
                y = i ? mean_rate[i-1].y : d.y,
                stderr = i ? mean_rate[i-1].stderr : d.stderr,
                x0 = xScale(x),
                x1 = xScale(d.x),
                y0min = yScale(y - stderr),
                y0max = yScale(y + stderr),
                y1min = yScale(d.y - stderr),
                y1max = yScale(d.y + stderr);
            return "M" + x0 + "," + y0min +
                "L" + x0 + "," + y0max +
                "L" + x1 + "," + y1max +
                "L" + x1 + "," + y1min +
                "L" + x0 + "," + y0min;
        }

        rate_svg.selectAll(".slice.mean_rates")
            .data(mean_rate)
            .enter().append("path")
            .attr("class", "slice_dataset_"+group_ids[group_idx])
            .attr("fill", p(group_idx))
            .attr("fill-opacity", "0.4")
            .attr("stroke", "none")
            .attr("d", slice);

        rate_svg.append("path")
            .attr("id", parent_id+"-group-"+group_ids[group_idx])
            .datum(mean_rate)
            .attr("class", "data-line")
            .style("stroke", p(group_idx))
            .attr("d", line);
        rate_svg.append("text")
            .attr("class","legend-label")
            .attr("x",width-max_length*7)
            .attr("y",margin.top+group_idx*20)
            .style("fill", p(group_idx))
            .text(group_names[group_idx]);
    }

    rate_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    rate_svg.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_notes=[];
    var event_lines=[];
    var event_areas=[];
    for(var i=0; i<event_types.length; i++)
    {
        var event_type=event_types[i];
        var times=[];
        for(var k=0; k<group_ids.length; k++)
        {
            var group_id=group_ids[k];
            var group_times=[];
            var realigned_trial_events=group_trial_events.get(group_id)
            for(var j=0; j<realigned_trial_events.length; j++)
            {
                if(realigned_trial_events[j].name==event_type)
                    group_times.push(realigned_trial_events[j].t);
            }
            times.push(d3.mean(group_times));
        }
        var mean_time=d3.mean(times);
        var min_time=d3.min(times);
        var max_time=d3.max(times);
        event_lines.push(
            rate_svg.append("line")
                .attr("x1", xScale(mean_time))
                .attr("y1", yScale(0))
                .attr("x2", xScale(mean_time))
                .attr("y2", yScale(max_rate +.1*max_rate))
                .classed("annotation-line",true)
        );
        var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
        event_areas.push(
            rate_svg.append("line")
                .attr("x1", area_x)
                .attr("y1", yScale(0))
                .attr("x2", area_x)
                .attr("y2", yScale(max_rate +.1*max_rate))
                .classed("annotation-line",true)
                .style("stroke", p(i))
                .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
        );
        event_notes.push(
            rate_svg.selectAll(".g-note")
                .data([event_type])
                .enter().append("text")
                .classed("annotation-text",true)
                .style('fill', p(i))
                .attr("x", xScale(mean_time))
                .attr("y", yScale(max_rate +.1*max_rate))
                .attr("dy", function(d, i) { return i * 1.3 + "em"; })
                .text(function(d) { return d; })
                .on("click", function(d) {
                    d3.select("#align_event").node().value= d;
                    dispatch.statechange();
                })
        );
    }

    var focus = rate_svg.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 4.5);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".35em");

    rate_svg.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    function mousemove() {
        var x0 = xScale.invert(d3.mouse(this)[0]);
        var y0 = yScale.invert(d3.mouse(this)[1]);
        min_y_dist=10000;
        min_y_d=null;
        for(var j=0; j<group_ids.length; j++)
        {
            rate=mean_rates.get(group_ids[j]);
            var i = bisectTime(rate, x0, 1);
            d0 = rate[i - 1];
            d1 = rate[i];
            d = x0 - d0.x > d1.x - x0 ? d1 : d0;
            y_dist=Math.abs(d.y-y0);
            if(y_dist<min_y_dist)
            {
                min_y_dist=y_dist;
                min_y_d=d;
            }
        }
        focus.attr("transform", "translate(" + xScale(min_y_d.x) + "," + yScale(min_y_d.y) + ")");
        focus.select("text").text(min_y_d.y.toFixed(2)+'Hz');
    }

    rate_svg.update=function update(realigned_mean_rates, realigned_trial_events){
        binwidth = parseInt(d3.select("#binwidth").node().value);
        kernelwidth = parseInt(d3.select("#kernelwidth").node().value);
        var min_time=10000;
        var max_time=-10000;
        var max_rate=0;
        mean_rates=realigned_mean_rates;
        for(var i=0; i<group_ids.length; i++)
        {
            var group_id=group_ids[i];
            var rate=mean_rates.get(group_id);
            var group_min_time=d3.min(rate, function(d){ return d.x; });
            var group_max_time=d3.max(rate, function(d){ return d.x; });
            if(group_min_time<min_time)
                min_time=group_min_time;
            if(group_max_time>max_time)
                max_time=group_max_time;
            var group_max_rate=d3.max(rate, function(d){ return d.y+d.stderr });
            if(group_max_rate>max_rate)
                max_rate=group_max_rate;

        }

        yScale.domain([0, max_rate +.1*max_rate]);
        yAxis.scale(yScale);
        xScale.domain([min_time, max_time]);
        xAxis.scale(xScale);

        xBinwidth =  width / (rate.length-1)
        for(var i=0; i<event_types.length; i++)
        {
            var event_type=event_types[i];
            var times=[];
            for(var k=0; k<group_ids.length; k++)
            {
                var group_id=group_ids[k];
                var group_times=[];
                var trial_events=realigned_trial_events.get(group_id);
                for(var j=0; j<trial_events.length; j++)
                {
                    if(trial_events[j].name==event_type)
                        group_times.push(trial_events[j].t);
                }
                times.push(d3.mean(group_times));
            }
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_lines[i]
                .attr("x1", xScale(mean_time))
                .attr("x2",xScale(mean_time));
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_areas[i]
                .attr("x1", area_x)
                .attr("x2", area_x)
                .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
            event_notes[i].attr("x", xScale(mean_time))
        }

        for(var i=0; i<group_ids.length; i++)
        {
            var group_id=group_ids[i];
            var mean_rate=mean_rates.get(group_id);
            rate_svg.selectAll('#'+parent_id+'-group-'+group_id).datum(mean_rate)
                .transition().duration(1000)
                .attr("class", "data-line")
                .attr("d", line);
            var slice = function(d,i) {
                var x = i ? mean_rate[i-1].x : d.x,
                    y = i ? mean_rate[i-1].y : d.y,
                    stderr = i ? mean_rate[i-1].stderr : d.stderr,
                    x0 = xScale(x),
                    x1 = xScale(d.x),
                    y0min = yScale(y - stderr),
                    y0max = yScale(y + stderr),
                    y1min = yScale(d.y - stderr),
                    y1max = yScale(d.y + stderr);
                return "M" + x0 + "," + y0min +
                    "L" + x0 + "," + y0max +
                    "L" + x1 + "," + y1max +
                    "L" + x1 + "," + y1min +
                    "L" + x0 + "," + y0min;
            }
            rate_svg.selectAll(".slice_dataset_"+group_id).remove();
            rate_svg.selectAll(".slice.mean_rates")
                .data(mean_rate)
                .enter().append("path")
                .attr("class", "slice_dataset_"+group_id)
                .attr("fill", p(i))
                .attr("fill-opacity", "0.4")
                .attr("stroke", "none")
                .attr("d", slice);
        }
        rate_svg.selectAll(".text").data(hist).remove();
        rate_svg.select(".y.axis").call(yAxis);
        rate_svg.select(".x.axis").call(xAxis);

    }
    dispatch.on("realigned.rate.population."+parent_id, rate_svg.update);
    return rate_svg;
}
