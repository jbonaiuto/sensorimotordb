var bisectTime = d3.bisector(function(d) { return d.x; }).left;
var p=d3.scale.category10();

var dispatch=d3.dispatch("statechange","realigned");

function drawRaster(parent_id, trial_spikes, trial_events, event_types)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50},
        width = scaleFactor*(960 - margin.left - margin.right),
        height = scaleFactor*(250 - margin.top - margin.bottom);

    var raster_svg = d3.select('#'+parent_id).append('svg:svg')
        .attr('width', width + margin.right + margin.left)
        .attr('height', height + margin.top + margin.bottom);

    var origin_transform=raster_svg
        .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var data={
        'spikes': trial_spikes,
        'events': trial_events
    };

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

    var absTrialNumbers=[];
    // Convert absolute trial numbers to relative
    for(var i=0; i<data.events.length; i++)
    {
        if($.inArray(data.events[i].trial, absTrialNumbers)<0)
        {
            absTrialNumbers.push(data.events[i].trial);
        }
    }
    for(var i=0; i<data.spikes.length; i++)
    {
        if($.inArray(data.spikes[i].y, absTrialNumbers)<0)
        {
            absTrialNumbers.push(data.spikes[i].y);
        }
    }
    absTrialNumbers.sort((a, b) => a - b);
    for(var i=0; i<data.events.length; i++)
    {
        data.events[i].relTrial=absTrialNumbers.indexOf(data.events[i].trial)+1;
    }
    for(var i=0; i<data.spikes.length; i++)
    {
        data.spikes[i].relTrial=absTrialNumbers.indexOf(data.spikes[i].y)+1;
    }

    // Scale the range of the data
    xScale.domain([d3.min([d3.min(data.events,function(d){return d.t}),d3.min(data.spikes,function(d){return d.x})]),
        d3.max([d3.max(data.events,function(d){return d.t}),d3.max(data.spikes,function(d){return d.x})])]);
    yScale.domain([d3.min([d3.min(data.events,function(d){return d.relTrial}),d3.min(data.spikes, function(d) { return d.relTrial; })]),
        d3.max([d3.max(data.events,function(d){return d.relTrial}),d3.max(data.spikes, function(d) { return d.relTrial; })])]);

    var raster=origin_transform.append("g")
        .attr("class", "raster");

    raster.selectAll("circle")
        .data(data.spikes)
        .enter().append("svg:circle")
        .attr("transform", function (d) { return "translate("+xScale(d.x)+", "+yScale(d.relTrial)+")"})
        .attr("r", 1);

    var events = origin_transform.append("g")
        .attr("class","events");

    var event_circles=events.selectAll("circle")
        .data(data.events)
        .enter().append("svg:circle")
        .attr("transform", function (d) { return "translate("+xScale(d.t)+", "+yScale(d.relTrial)+")"})
        .attr("r", 4)
        .style('fill', function (d) {return p(event_types.indexOf(d.name))})
        .on("mouseover", function(d) {
            focus.attr("transform", "translate(" + xScale(d.t) + "," + yScale(d.relTrial) + ")");
            focus.select("text").text(d.name);
            focus.style("display","")
        })
        .on("click", function(d) {
            d3.select("#align_event").node().value= d.name;
            dispatch.statechange();
        });

    var focus = origin_transform.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 6);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".5em");

    origin_transform.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    origin_transform.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Trial");

    raster_svg.update=function update(realigned_spikes, realigned_trial_events)
    {
        data.spikes=realigned_spikes;
        data.events=realigned_trial_events;
        focus.style("display","none");

        var absTrialNumbers=[];
        // Convert absolute trial numbers to relative
        for(var i=0; i<data.events.length; i++)
        {
            if($.inArray(data.events[i].trial, absTrialNumbers)<0)
            {
                absTrialNumbers.push(data.events[i].trial);
            }
        }
        for(var i=0; i<data.spikes.length; i++)
        {
            if($.inArray(data.spikes[i].y, absTrialNumbers)<0)
            {
                absTrialNumbers.push(data.spikes[i].y);
            }
        }
        absTrialNumbers.sort((a, b) => a - b);
        for(var i=0; i<data.events.length; i++)
        {
            data.events[i].relTrial=absTrialNumbers.indexOf(data.events[i].trial)+1;
        }
        for(var i=0; i<data.spikes.length; i++)
        {
            data.spikes[i].relTrial=absTrialNumbers.indexOf(data.spikes[i].y)+1;
        }

        xScale.domain([d3.min([d3.min(data.events,function(d){return d.t}),d3.min(data.spikes,function(d){return d.x})]),
            d3.max([d3.max(data.events,function(d){return d.t}),d3.max(data.spikes,function(d){return d.x})])]);
        xAxis.scale(xScale);

        origin_transform.selectAll("circle")
            .data(data.spikes)
            .attr("transform", function (d) { return "translate("+xScale(d.x)+", "+yScale(d.relTrial)+")"});

        events.selectAll("circle")
            .data(data.events)
            .attr("transform", function (d) { return "translate("+xScale(d.t)+", "+yScale(d.relTrial)+")"})

        origin_transform.select(".x.axis").call(xAxis);
    };

    return raster_svg;
}

function drawHistogram(parent_id, trial_spikes, trial_events, event_types)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scaleFactor*(960 - margin.left - margin.right)
        , height = scaleFactor*(200 - margin.top - margin.bottom);

    var histo_svg = d3.select('#'+parent_id).append('svg:svg')
        .attr('width', width + margin.right + margin.left)
        .attr('height', height + margin.top + margin.bottom);

    var origin_transform=histo_svg
        .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var data={
        'spikes': trial_spikes,
        'events': trial_events
    };

    var binwidth = parseInt(d3.select("#binwidth").node().value);

    var timeMin=d3.min([d3.min(data.events,function(d){return d.t}),d3.min(data.spikes,function(d){return d.x})]);
    var timeMax=d3.max([d3.max(data.events,function(d){return d.t}),d3.max(data.spikes,function(d){return d.x})]);

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

    var numTrials=d3.max(data.spikes, function(d){ return d.y});

    var hist = d3.layout.histogram()
        .bins(d3.range(xScale.domain()[0], xScale.domain()[1]+binwidth, binwidth))
        (data.spikes.map(function(d) {return d.x; }));

    var scaledHist=[];
    for(var j=0; j<hist.length; j++)
        scaledHist.push({
            x: hist[j].x,
            y: hist[j].y/numTrials/(binwidth/1000.0)
        });

    var xBinwidth = width / (scaledHist.length -1);
    var yMax=d3.max(scaledHist, function(d) { return d.y+1; });
    yScale.domain([0, yMax +.1*yMax])

    origin_transform.selectAll(".histo-bar")
        .data(scaledHist)
        .enter().append("rect")
        .attr("class", "histo-bar")
        .attr("width", function(d) { return xBinwidth })
        .attr("height", function(d) { return d3.max([0,height- yScale(d.y)-1]); })
        .attr("x", function(d) {return xScale(d.x)})
        .attr("y", function(d) {return yScale(d.y)});

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_elems={
        notes: new Map(),
        lines: new Map(),
        areas: new Map()
    };
    for(var event_type_idx=0; event_type_idx<event_types.length; event_type_idx++)
    {
        var event_type=event_types[event_type_idx];
        var times=[];
        for(let trial_event of data.events)
        {
            if(trial_event.name==event_type)
                times.push(trial_event.t);
        }
        if(times.length>0)
        {
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_elems.lines.set(event_type,
                origin_transform.append("line")
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(0))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
            );
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_elems.areas.set(event_type,
                origin_transform.append("line")
                    .attr("x1", area_x)
                    .attr("y1", yScale(0))
                    .attr("x2", area_x)
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
                    .style("stroke", p(event_type_idx))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
            );
            event_elems.notes.set(event_type,
                origin_transform.selectAll(".g-note")
                    .data([event_type])
                    .enter().append("text")
                    .classed("annotation-text",true)
                    .style('fill', p(event_type_idx))
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
    origin_transform.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    // draw the x axis
    origin_transform.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    var old_binwidth = binwidth;
    var old_xBinwidth = xBinwidth;

    histo_svg.update=function update(realigned_spikes, realigned_trial_events)
    {
        data.spikes=realigned_spikes;
        data.events=realigned_trial_events;

        binwidth = parseInt(d3.select("#binwidth").node().value);

        var timeMin=d3.min([d3.min(data.events,function(d){return d.t}),d3.min(data.spikes,function(d){return d.x})]);
        var timeMax=d3.max([d3.max(data.events,function(d){return d.t}),d3.max(data.spikes,function(d){return d.x})]);

        xScale.domain([timeMin, timeMax]);
        xAxis.scale(xScale);

        var hist = d3.layout.histogram()
            .bins(d3.range(xScale.domain()[0], xScale.domain()[1]+binwidth, binwidth))
            (data.spikes.map(function(d) {return d.x; }));

        scaledHist=[];
        for(var j=0; j<hist.length; j++)
            scaledHist.push({
                x: hist[j].x,
                y: hist[j].y/numTrials/(binwidth/1000.0)
            });

        var yMax=d3.max(scaledHist, function(d) { return d.y+1; });
        yScale.domain([0, yMax +.1*yMax]);
        xBinwidth =  width / (scaledHist.length-1);

        var xEase = "cubic-in-out";
        var yEase = "bounce";

        origin_transform.selectAll(".histo-bar").data(scaledHist)
            .enter().append("rect")
            .attr("class", "histo-bar")
            .attr("fill", "white")
            .attr("height", function(d) { return d3.max([0,height- yScale(d.y)-1]); })
            .attr("width", function(d) { return old_xBinwidth; })
            .attr("x", function(d) {return xScale(d.x) * old_binwidth / binwidth})
            .attr("y", function(d) {return yScale(d.y)});

        origin_transform.selectAll(".histo-bar").data(scaledHist)
            .transition().duration(1000).ease(yEase)
            .attr("y", function(d) {return yScale(d.y)})
            .attr("height", function(d) { return d3.max([0,height- yScale(d.y)-1]); })
            .attr("fill", function (d) {return "hsl(" + (1-(d.y-yScale.domain()[0])/(yScale.domain()[1]-yScale.domain()[0]))*255 + ", 85%, 75%)"})
            .transition().duration(1000).ease(xEase)
            .attr("x", function(d) {return xScale(d.x)})
            .attr("width", function(d) { return xBinwidth; });

        origin_transform.selectAll(".histo-bar").data(scaledHist).exit()
            .transition().duration(1000).ease(yEase)
            .attr("y", function(d) {return yScale(d.y)})
            .attr("height", function(d) { return d3.max([0,height- yScale(d.y)-1]); })
            .transition().duration(1000).ease(xEase)
            .attr("width", function(d) { return xBinwidth; })
            .attr("x", function(d) {return xScale(d.x) * binwidth / old_binwidth})
            .remove();

        for(let event_type of event_types)
        {
            var times=[];
            for(let trial_event of data.events)
            {
                if(trial_event.name==event_type)
                    times.push(trial_event.t);
            }
            if(times.length>0)
            {
                var mean_time=d3.mean(times);
                var min_time=d3.min(times);
                var max_time=d3.max(times);
                var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
                if(event_elems.notes.has(event_type))
                {
                    event_elems.lines.get(event_type)
                        .attr("x1", xScale(mean_time))
                        .attr("x2",xScale(mean_time))
                        .attr("y2", yScale(yMax +.1*yMax));
                    event_elems.areas.get(event_type)
                        .attr("x1", area_x)
                        .attr("x2", area_x)
                        .attr("y2", yScale(yMax +.1*yMax))
                        .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                    event_elems.notes.get(event_type)
                        .attr("x", xScale(mean_time))
                        .attr("y", yScale(yMax +.1*yMax));
                }
            }
        }
        origin_transform.select(".y.axis").call(yAxis);
        origin_transform.select(".x.axis").call(xAxis);

        old_binwidth = binwidth;
        old_xBinwidth = xBinwidth;

    };

    return histo_svg;

}

function drawFiringRate(parent_id, trial_rate, trial_events, event_types)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scaleFactor*(960 - margin.left - margin.right)
        , height = scaleFactor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#"+parent_id).append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var origin_transform=rate_svg
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var data={
        'rate': trial_rate,
        'events': trial_events
    };

    var timeMin=d3.min([d3.min(data.events,function(d){return d.t}),d3.min(data.rate,function(d){return d.x})]);
    var timeMax=d3.max([d3.max(data.events,function(d){return d.t}),d3.max(data.rate,function(d){return d.x})]);

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


    var yMax=d3.max(data.rate, function(d) { return d.y+1; });
    yScale.domain([0, yMax +.1*yMax])

    origin_transform.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    origin_transform.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    origin_transform.append("path")
        .datum(data.rate)
        .attr("class", "data-line")
        .attr("d", line);

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_elems={
        'notes': new Map(),
        'lines': new Map(),
        'areas': new Map()
    };

    for(var event_type_idx=0; event_type_idx<event_types.length; event_type_idx++)
    {
        var event_type=event_types[event_type_idx];
        var times=[];
        for(let trial_event of data.events)
        {
            if(trial_event.name==event_type)
                times.push(trial_event.t);
        }
        if(times.length>0)
        {
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_elems.lines.set(event_type,
                origin_transform.append("line")
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(0))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
            );
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_elems.areas.set(event_type,
                origin_transform.append("line")
                    .attr("x1", area_x)
                    .attr("y1", yScale(0))
                    .attr("x2", area_x)
                    .attr("y2", yScale(yMax +.1*yMax))
                    .classed("annotation-line",true)
                    .style("stroke", p(event_type_idx))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
            );
            event_elems.notes.set(event_type,
                origin_transform.selectAll(".g-note")
                    .data([event_type])
                    .enter().append("text")
                    .classed("annotation-text",true)
                    .style('fill', p(event_type_idx))
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

    var focus = origin_transform.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 4.5);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".35em");

    origin_transform.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    function mousemove()
    {
        var x0 = xScale.invert(d3.mouse(this)[0]);
        var i = bisectTime(data.rate, x0, 1);
        var d0 = data.rate[i - 1];
        var d1 = data.rate[i];
        var d = x0 - d0.x > d1.x - x0 ? d1 : d0;
        focus.attr("transform", "translate(" + xScale(d.x) + "," + yScale(d.y) + ")");
        focus.select("text").text(d.y.toFixed(2)+'Hz');
    }

    rate_svg.update=function update(realigned_rate, realigned_trial_events)
    {
        data.rate=realigned_rate;
        data.events=realigned_trial_events;

        var yMax=d3.max(data.rate, function(d) { return d.y+1; });
        yScale.domain([0, yMax +.1*yMax]);
        yAxis.scale(yScale);

        var timeMin=d3.min([d3.min(data.events,function(d){return d.t}),d3.min(data.rate,function(d){return d.x})]);
        var timeMax=d3.max([d3.max(data.events,function(d){return d.t}),d3.max(data.rate,function(d){return d.x})]);

        xScale.domain([timeMin, timeMax]);
        xAxis.scale(xScale);

        for(let event_type of event_types)
        {
            var times=[];
            for(let trial_event of data.events)
            {
                if(trial_event.name==event_type)
                    times.push(trial_event.t);
            }
            if(times.length>0)
            {
                var mean_time=d3.mean(times);
                var min_time=d3.min(times);
                var max_time=d3.max(times);
                var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
                if(event_elems.notes.has(event_type))
                {
                    event_elems.lines.get(event_type)
                        .attr("x1", xScale(mean_time))
                        .attr("x2",xScale(mean_time))
                        .attr("y2", yScale(yMax +.1*yMax));
                    event_elems.areas.get(event_type)
                        .attr("x1", area_x)
                        .attr("x2", area_x)
                        .attr("y2", yScale(yMax +.1*yMax))
                        .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                    event_elems.notes.get(event_type)
                        .attr("x", xScale(mean_time))
                        .attr("y", yScale(yMax +.1*yMax));
                }
            }
        }

        origin_transform.selectAll('.data-line').datum(data.rate)
            .transition().duration(1000)
            .attr("class", "data-line")
            .attr("d", line);

        origin_transform.select(".y.axis").call(yAxis);
        origin_transform.select(".x.axis").call(xAxis);
    };

    return rate_svg;
}

function drawPopulationFiringRate(parent_id, legend_id, group_trial_rates, group_trial_events, event_types, groups,
                                  scale_factor)
{
    var margin = {top: 30, right: 0, bottom: 40, left: 50}
        , width = scale_factor*(700 - margin.left - margin.right)
        , height = scale_factor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#"+parent_id)
        .append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var origin_transform=rate_svg
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var group_data={
        'rates': group_trial_rates,
        'events': group_trial_events
    };

    var min_times=[];
    var max_times=[];
    var min_rates=[];
    var max_rates=[];
    for(let group_id of groups.keys())
    {
        if(group_data.rates.get(group_id)!=null)
        {
            var rate=group_data.rates.get(group_id);
            var events=group_data.events.get(group_id);
            min_times.push(d3.min([d3.min(events,function(d){return d.t}),d3.min(rate,function(d){return d.x})]));
            max_times.push(d3.max([d3.max(events,function(d){return d.t}),d3.max(rate,function(d){return d.x})]));
            min_rates.push(d3.min(rate, function(d){ return d.y-1 }));
            max_rates.push(d3.max(rate, function(d){ return d.y+1 }));
        }
    }
    var min_time=d3.min(min_times);
    var max_time=d3.max(max_times);
    var min_rate=d3.min(min_rates);
    var max_rate=d3.max(max_rates);

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


    yScale.domain([min_rate-0.1*Math.abs(min_rate), max_rate +.1*Math.abs(max_rate)]);

    origin_transform.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    origin_transform.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    var max_length=d3.max(Array.from(groups.values()), function(d){return d.length});
    $('#'+legend_id).height(scale_factor*(400 - margin.bottom));

    var legend_svg = d3.select('#'+legend_id)
        .append("svg")
        .attr("width", 40+max_length*7)
        .attr("height", 20*(groups.size+1));

    var legend = legend_svg.append("g")
        .attr("class", "legend1")
        .attr('transform', 'translate(-20,50)');

    for(var group_idx=0; group_idx<groups.size; group_idx++)
    {
        var group_id=Array.from(groups.keys())[group_idx];
        if(group_data.rates.get(group_id)!=null)
        {
            var group_name=groups.get(group_id);
            origin_transform.append("path")
                .attr("id", parent_id+"-group-"+group_id)
                .datum(group_data.rates.get(group_id))
                .attr("class", "data-line")
                .style("stroke", p(group_idx))
                .attr("d", line);
            legend.append("text")
                .attr("id",parent_id+"-label-group-"+group_id)
                .attr("group_id",group_id)
                .attr("class","legend-label")
                .attr("x", 40)
                .attr("y", (group_idx-1) *  20 + 5)
                .style("fill", p(group_idx))
                .text(group_name)
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
    }

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_elems={
        'notes': new Map(),
        'lines': new Map(),
        'areas': new Map()
    };

    for(var event_type_idx=0; event_type_idx<event_types.length; event_type_idx++)
    {
        var event_type=event_types[event_type_idx];
        var times=[];
        for(let group_id of groups.keys())
        {
            var group_times=[];
            if(group_data.events.get(group_id)!=null)
            {
                var realigned_trial_events=group_data.events.get(group_id)
                for(var j=0; j<realigned_trial_events.length; j++)
                {
                    if(realigned_trial_events[j].name==event_type)
                        group_times.push(realigned_trial_events[j].t);
                }
                if(group_times.length>0)
                    times.push(d3.mean(group_times));
            }
        }
        if(times.length>0)
        {
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            event_elems.lines.set(event_type,
                origin_transform.append("line")
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)))
                    .classed("annotation-line",true)
            );
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            event_elems.areas.set(event_type,
                origin_transform.append("line")
                    .attr("x1", area_x)
                    .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                    .attr("x2", area_x)
                    .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)))
                    .classed("annotation-line",true)
                    .style("stroke", p(event_type_idx))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
            );
            event_elems.notes.set(event_type,
                origin_transform.selectAll(".g-note")
                    .data([event_type])
                    .enter().append("text")
                    .classed("annotation-text",true)
                    .style('fill', p(event_type_idx))
                    .attr("x", xScale(mean_time))
                    .attr("y", yScale(max_rate+0.1*Math.abs(max_rate)))
                    .attr("dy", function(d, i) { return i * 1.3 + "em"; })
                    .text(function(d) { return d; })
                    .on("click", function(d) {
                        d3.select("#align_event").node().value= d;
                        dispatch.statechange();
                    })
            );
        }
    }

    var focus = origin_transform.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 4.5);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".35em");

    origin_transform.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    function mousemove()
    {
        var x0 = xScale.invert(d3.mouse(this)[0]);
        var y0 = yScale.invert(d3.mouse(this)[1]);
        var min_y_dist=10000;
        var min_y_d=null;
        for(let group_id of groups.keys())
        {
            if(group_data.rates.get(group_id)!=null)
            {
                var rate=group_data.rates.get(group_id);
                var i = bisectTime(rate, x0, 1);
                if(i<rate.length)
                {
                    var d0 = rate[i - 1];
                    var d1 = rate[i];
                    var d = x0 - d0.x > d1.x - x0 ? d1 : d0;
                    var y_dist=Math.abs(d.y-y0);
                    if(y_dist<min_y_dist)
                    {
                        min_y_dist=y_dist;
                        min_y_d=d;
                    }
                }
            }
        }
        focus.attr("transform", "translate(" + xScale(min_y_d.x) + "," + yScale(min_y_d.y) + ")");
        focus.select("text").text(min_y_d.y.toFixed(2)+'Hz');
    }

    rate_svg.update=function update(realigned_rates, realigned_trial_events)
    {
        group_data.rates=realigned_rates;
        group_data.events=realigned_trial_events
        var min_times=[];
        var max_times=[];
        var min_rates=[];
        var max_rates=[];
        for(let group_id of groups.keys())
        {
            var rate=group_data.rates.get(group_id);
            var events=group_data.events.get(group_id);
            min_times.push(d3.min([d3.min(events,function(d){return d.t}),d3.min(rate,function(d){return d.x})]));
            max_times.push(d3.max([d3.max(events,function(d){return d.t}),d3.max(rate,function(d){return d.x})]));
            min_rates.push(d3.min(rate, function(d){ return d.y-1 }));
            max_rates.push(d3.max(rate, function(d){ return d.y+1 }));
        }
        var min_time=d3.min(min_times);
        var max_time=d3.max(max_times);
        var min_rate=d3.min(min_rates);
        var max_rate=d3.max(max_rates);

        yScale.domain([min_rate-0.1*Math.abs(min_rate), max_rate+0.1*Math.abs(max_rate)]);
        yAxis.scale(yScale);
        xScale.domain([min_time, max_time]);
        xAxis.scale(xScale);

        for(let event_type of event_types)
        {
            var times=[];
            for(let group_id of groups.keys())
            {
                if(group_data.events.get(group_id)!=null)
                {
                    var group_times=[];
                    var trial_events=group_data.events.get(group_id);
                    for(let trial_event of trial_events)
                    {
                        if(trial_event.name==event_type)
                            group_times.push(trial_event.t);
                    }
                    if(group_times.length>0)
                        times.push(d3.mean(group_times));
                }
            }
            if(times.length>0)
            {
                var mean_time=d3.mean(times);
                var min_time=d3.min(times);
                var max_time=d3.max(times);
                var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
                if(event_elems.notes.has(event_type))
                {
                    event_elems.lines.get(event_type)
                        .attr("x1", xScale(mean_time))
                        .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                        .attr("x2",xScale(mean_time))
                        .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)));
                    event_elems.areas.get(event_type)
                        .attr("x1", area_x)
                        .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                        .attr("x2", area_x)
                        .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)))
                        .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                    event_elems.notes.get(event_type)
                        .attr("x", xScale(mean_time))
                        .attr("y", yScale(max_rate+0.1*Math.abs(max_rate)));
                }
            }
        }

        for(let group_id of groups.keys())
        {
            if(group_data.rates.get(group_id)!=null)
            {
                origin_transform.selectAll('#'+parent_id+'-group-'+group_id).datum(group_data.rates.get(group_id))
                    .transition().duration(1000)
                    .attr("class", "data-line")
                    .attr("d", line);
            }
        }
        origin_transform.selectAll(".text").data(hist).remove();
        origin_transform.select(".y.axis").call(yAxis);
        origin_transform.select(".x.axis").call(xAxis);

    };

    dispatch.on("realigned.rate.population."+parent_id, rate_svg.update);

    d3.select("#"+parent_id+"_generate")
        .on("click", writeDownloadLink);

    function writeDownloadLink(){
        try {
            var isFileSaverSupported = !!new Blob();
        } catch (e) {
            alert("blob not supported");
        }

        var html = rate_svg
            .attr("title", "test2")
            .attr("version", 1.1)
            .attr("xmlns", "http://www.w3.org/2000/svg")
            .node().outerHTML;

        var blob = new Blob([html], {type: "image/svg+xml"});
        saveAs(blob, parent_id+".svg");
    };
    return rate_svg;
}

function drawMeanNormalizedFiringRates(parent_id, legend_id, group_mean_rates, group_trial_events, event_types, groups, scale_factor)
{
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scale_factor*(960 - margin.left - margin.right)
        , height = scale_factor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#"+parent_id).append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    var origin_transform=rate_svg
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var group_data={
        'rates': group_mean_rates,
        'events': group_trial_events
    };
    var min_times=[];
    var max_times=[];
    var min_rates=[];
    var max_rates=[];

    for(let group_id of groups.keys())
    {
        if(group_data.rates.get(group_id)!=null)
        {
            var rate=group_data.rates.get(group_id);
            var events=group_data.events.get(group_id);
            //min_times.push(d3.min([d3.min(events,function(d){return d.t}),d3.min(rate,function(d){return d.x})]));
            min_times.push(d3.min(events,function(d){return d.t}));
            //max_times.push(d3.max([d3.max(events,function(d){return d.t}),d3.max(rate,function(d){return d.x})]));
            max_times.push(d3.max(rate,function(d){return d.x}));
            min_rates.push(d3.min(rate, function(d){ return d.y- d.stderr }))
            max_rates.push(d3.max(rate, function(d){ return d.y+ d.stderr }))
        }
    }
    var min_time=d3.min(min_times);
    var max_time=d3.max(max_times);
    var min_rate=d3.min(min_rates);
    var max_rate=d3.max(max_rates);

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

    yScale.domain([min_rate-0.1*Math.abs(min_rate), max_rate+0.1*Math.abs(max_rate)]);

    origin_transform.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    origin_transform.append("svg:g")
        .attr("class", "y axis")
        .call(yAxis);

    var max_length=d3.max(Array.from(groups.values()), function(d){return d.length});

    var legend_svg = d3.select('#'+legend_id)
        .append("svg")
        .attr("width", 40+max_length*7)
        .attr("height", 20*(groups.size+1));

    var legend = legend_svg.append("g")
        .attr("class", "legend1")
        .attr('transform', 'translate(-20,50)');

    for(var group_idx=0; group_idx<groups.size; group_idx++)
    {
        var group_id=Array.from(groups.keys())[group_idx];
        var group_name=groups.get(group_id);
        if(group_data.rates.get(group_id)!=null)
        {
            var mean_rate=group_data.rates.get(group_id);

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
            };

            origin_transform.selectAll(".slice.mean_rates")
                .data(mean_rate)
                .enter().append("path")
                .attr("class", "slice_dataset_"+group_id)
                .attr("fill", p(group_idx))
                .attr("fill-opacity", "0.4")
                .attr("stroke", "none")
                .attr("d", slice);

            origin_transform.append("path")
                .attr("id", parent_id+"-group-"+group_id)
                .datum(mean_rate)
                .attr("class", "data-line")
                .style("stroke", p(group_idx))
                .attr("d", line);

            legend.append("text")
                .attr("id",parent_id+"-label-group-"+group_id)
                .attr("group_id",group_id)
                .attr("class","legend-label")
                .attr("x", 40)
                .attr("y", (group_idx-1) *  20 + 5)
                .style("fill", p(group_idx))
                .text(group_name)
        }
    }

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", width/2)
        .attr("y", height + margin.bottom)
        .text("Time (ms)");

    origin_transform.append("text")
        .attr("class", "axis-label")
        .attr("text-anchor", "middle")
        .attr("x", -height/2)
        .attr("y", -(margin.left-3))
        .attr("dy", ".75em")
        .attr("transform", "rotate(-90)")
        .text("Firing Rate (Hz)");

    // Events
    var event_elems={
        'notes': new Map(),
        'lines': new Map(),
        'areas': new Map()
    };

    for(var event_type_idx=0; event_type_idx<event_types.length; event_type_idx++)
    {
        var event_type=event_types[event_type_idx];
        var times=[];
        for(let group_id of groups.keys())
        {
            if(group_data.events.get(group_id)!=null)
            {
                var group_times=[];
                var realigned_trial_events=group_data.events.get(group_id)
                for(let trial_event of realigned_trial_events)
                {
                    if(trial_event.name==event_type)
                        group_times.push(trial_event.t);
                }
                times.push(d3.mean(group_times));
            }
        }
        var mean_time=d3.mean(times);
        var min_time=d3.min(times);
        var max_time=d3.max(times);
        event_elems.lines.set(event_type,
            origin_transform.append("line")
                .attr("x1", xScale(mean_time))
                .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                .attr("x2", xScale(mean_time))
                .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)))
                .classed("annotation-line",true)
        );
        var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
        event_elems.areas.set(event_type,
            origin_transform.append("line")
                .attr("x1", area_x)
                .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                .attr("x2", area_x)
                .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)))
                .classed("annotation-line",true)
                .style("stroke", p(event_type_idx))
                .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px")
        );
        event_elems.notes.set(event_type,
            origin_transform.selectAll(".g-note")
                .data([event_type])
                .enter().append("text")
                .classed("annotation-text",true)
                .style('fill', p(event_type_idx))
                .attr("x", xScale(mean_time))
                .attr("y", yScale(max_rate+0.1*Math.abs(max_rate)))
                .attr("dy", function(d, i) { return i * 1.3 + "em"; })
                .text(function(d) { return d; })
                .on("click", function(d) {
                    d3.select("#align_event").node().value= d;
                    dispatch.statechange();
                })
        );
    }

    var focus = origin_transform.append("g")
        .attr("class", "focus")
        .style("display", "none");

    focus.append("circle")
        .attr("r", 4.5);

    focus.append("text")
        .attr("x", 9)
        .attr("dy", ".35em");

    origin_transform.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    function mousemove()
    {
        var x0 = xScale.invert(d3.mouse(this)[0]);
        var y0 = yScale.invert(d3.mouse(this)[1]);
        var min_y_dist=10000;
        var min_y_d=null;
        for(let group_id of groups.keys())
        {
            if(group_data.rates.get(group_id)!=null)
            {
                var rate=group_data.rates.get(group_id);
                var i = bisectTime(rate, x0, 1);
                if(i<rate.length)
                {
                    var d0 = rate[i - 1];
                    var d1 = rate[i];
                    var d = x0 - d0.x > d1.x - x0 ? d1 : d0;
                    var y_dist=Math.abs(d.y-y0);
                    if(y_dist<min_y_dist)
                    {
                        min_y_dist=y_dist;
                        min_y_d=d;
                    }
                }
            }
        }
        focus.attr("transform", "translate(" + xScale(min_y_d.x) + "," + yScale(min_y_d.y) + ")");
        focus.select("text").text(min_y_d.y.toFixed(2)+'Hz');
    }

    rate_svg.update=function update(realigned_mean_rates, realigned_trial_events)
    {
        group_data.rates=realigned_mean_rates;
        group_data.events=realigned_trial_events;
        var min_times=[];
        var max_times=[];
        var min_rates=[];
        var max_rates=[];
        for(let group_id of groups.keys())
        {
            if(group_data.rates.get(group_id)!=null)
            {
                var rate=group_data.rates.get(group_id);
                var events=group_data.events.get(group_id);
                //min_times.push(d3.min([d3.min(events,function(d){return d.t}),d3.min(rate,function(d){return d.x})]));
                min_times.push(d3.min(events,function(d){return d.t}));
                //max_times.push(d3.max([d3.max(events,function(d){return d.t}),d3.max(rate,function(d){return d.x})]));
                max_times.push(d3.max(rate,function(d){return d.x}));
                min_rates.push(d3.min(rate, function(d){ return d.y-d.stderr }));
                max_rates.push(d3.max(rate, function(d){ return d.y+d.stderr }));
            }
        }
        var min_time=d3.min(min_times);
        var max_time=d3.max(max_times);
        var min_rate=d3.min(min_rates);
        var max_rate=d3.max(max_rates);

        yScale.domain([min_rate-0.1*Math.abs(min_rate), max_rate+0.1*Math.abs(max_rate)]);
        yAxis.scale(yScale);
        xScale.domain([min_time, max_time]);
        xAxis.scale(xScale);

        for(let event_type of event_types)
        {
            var times=[];
            for(let group_id of groups.keys())
            {
                if(group_data.events.get(group_id)!=null)
                {
                    var group_times=[];
                    var trial_events=group_data.events.get(group_id);
                    for(let trial_event of trial_events)
                    {
                        if(trial_event.name==event_type)
                            group_times.push(trial_event.t);
                    }
                    times.push(d3.mean(group_times));
                }
            }
            var mean_time=d3.mean(times);
            var min_time=d3.min(times);
            var max_time=d3.max(times);
            var area_x=xScale(min_time)+.5*(xScale(max_time)-xScale(min_time));
            if(event_elems.notes.has(event_type))
            {
                event_elems.lines.get(event_type)
                    .attr("x1", xScale(mean_time))
                    .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                    .attr("x2", xScale(mean_time))
                    .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)));
                event_elems.areas.get(event_type)
                    .attr("x1", area_x)
                    .attr("y1", yScale(min_rate-0.1*Math.abs(min_rate)))
                    .attr("x2", area_x)
                    .attr("y2", yScale(max_rate+0.1*Math.abs(max_rate)))
                    .style("stroke-width", (xScale(max_time)-xScale(min_time)+1)+"px");
                event_elems.notes.get(event_type)
                    .attr("x", xScale(mean_time))
                    .attr("y", yScale(max_rate+0.1*Math.abs(max_rate)));
            }
        }

        for(var group_idx=0; group_idx<groups.size; group_idx++)
        {
            var group_id=Array.from(groups.keys())[group_idx];
            if(group_data.rates.get(group_id)!=null)
            {
                var mean_rate=group_data.rates.get(group_id);
                origin_transform.selectAll('#'+parent_id+'-group-'+group_id).datum(mean_rate)
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
                origin_transform.selectAll(".slice_dataset_"+group_id).remove();
                origin_transform.selectAll(".slice.mean_rates")
                    .data(mean_rate)
                    .enter().append("path")
                    .attr("class", "slice_dataset_"+group_id)
                    .attr("fill", p(group_idx))
                    .attr("fill-opacity", "0.4")
                    .attr("stroke", "none")
                    .attr("d", slice);
            }
        }
        origin_transform.selectAll(".text").data(hist).remove();
        origin_transform.select(".y.axis").call(yAxis);
        origin_transform.select(".x.axis").call(xAxis);

    };

    dispatch.on("realigned.rate.population."+parent_id, rate_svg.update);

    d3.select("#"+parent_id+"_generate")
        .on("click", writeDownloadLink);

    function writeDownloadLink(){
        try {
            var isFileSaverSupported = !!new Blob();
        } catch (e) {
            alert("blob not supported");
        }

        var html = rate_svg
            .attr("title", "test2")
            .attr("version", 1.1)
            .attr("xmlns", "http://www.w3.org/2000/svg")
            .node().outerHTML;

        var blob = new Blob([html], {type: "image/svg+xml"});
        saveAs(blob, parent_id+".svg");
    };

    return rate_svg;
}
