var bisectTime = d3.bisector(function(d) { return d.x; }).left;
var p=d3.scale.category10();

function align_all_events(align_to)
{
    d3.select("#align_event").node().value= align_to;
    for(var j=0; j<condition_ids.length; j++)
    {
        func=d3.select('#align_event').on("change.rate.condition."+condition_ids[j]);
        func();

    }
    for(var j=0; j<unit_ids.length; j++)
    {
        func=d3.select('#align_event').on("change.rate.unit."+unit_ids[j]);
        func();

    }
}

function drawConditionPopulationFiringRate(condition_id, unit_trials, unit_trial_events, event_types, unit_ids)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scaleFactor*(960 - margin.left - margin.right)
        , height = scaleFactor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#condition-"+condition_id+"-plots").append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var binwidth = parseInt(d3.select("#binwidth").node().value);
    d3.selectAll("#binwidth").on("change.rate.condition."+condition_id, update);

    var align_event = d3.select("#align_event").node().value;
    d3.selectAll("#align_event").on("change.rate.condition."+condition_id, update);
    var rate_data=new Map();
    var min_time=10000;
    var max_time=-10000;
    var max_rate=0;
    for(var i=0; i<unit_ids.length; i++)
    {
        var unit_id=unit_ids[i];
        var realigned_unit_data=realign_spikes(unit_trials.get(unit_id), unit_trial_events.get(unit_id), align_event);
        var rate=get_firing_rate(realigned_unit_data, binwidth, width);
        rate_data.set(unit_id,rate);
        var unit_min_time=d3.min(rate, function(d){ return d.x; });
        var unit_max_time=d3.max(rate, function(d){ return d.x; });
        if(unit_min_time<min_time)
            min_time=unit_min_time;
        if(unit_max_time>max_time)
            max_time=unit_max_time;
        var unit_max_rate=d3.max(rate, function(d){ return d.y+1 });
        if(unit_max_rate>max_rate)
            max_rate=unit_max_rate;
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

    rate_svg.append("rect")
        .attr("class", "overlay")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() { focus.style("display", null); })
        .on("mouseout", function() { focus.style("display", "none"); })
        .on("mousemove", mousemove);

    for(var i=0; i<unit_ids.length; i++)
    {
        rate_svg.append("path")
            .attr("id", "condition-unit-"+unit_ids[i])
            .datum(rate_data.get(unit_ids[i]))
            .attr("class", "data-line")
            .style("stroke", p(i))
            .attr("d", line);
        rate_svg.append("text")
            .attr("class","legend-label")
            .attr("x",width-2*margin.left)
            .attr("y",margin.top+i*20)
            .style("fill", p(i))
            .text("Unit "+unit_ids[i])
            .on("click", function(d){
                document.location.href="/mirrordb/unit/"+d.id+"/";
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
    var realigned_unit_trials_events=new Map();
    for(var i=0; i<event_types.length; i++)
    {
        var event_type=event_types[i];
        var times=[];
        for(var k=0; k<unit_ids.length; k++)
        {
            var unit_id=unit_ids[k];
            var unit_times=[];
            if(realigned_unit_trials_events.get(unit_id)==null)
                realigned_unit_trials_events.set(unit_id,realign_events(unit_trial_events.get(unit_id), align_event));
            var realigned_trial_events=realigned_unit_trials_events.get(unit_id)
            for(var j=0; j<realigned_trial_events.length; j++)
            {
                if(realigned_trial_events[j].name==event_type)
                    unit_times.push(realigned_trial_events[j].t);
            }
            times.push(d3.mean(unit_times));
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
                    align_all_events(d);
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


    function mousemove() {
        var x0 = xScale.invert(d3.mouse(this)[0]);
        var y0 = yScale.invert(d3.mouse(this)[1]);
        min_y_dist=10000;
        min_y_d=null;
        for(var j=0; j<unit_ids.length; j++)
        {
            rate=rate_data.get(unit_ids[j]);
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

    function update(){
        binwidth = parseInt(d3.select("#binwidth").node().value);
        var align_event = d3.select("#align_event").node().value;
        rate_data=new Map();
        var min_time=10000;
        var max_time=-10000;
        var max_rate=0;
        for(var i=0; i<unit_ids.length; i++)
        {
            var unit_id=unit_ids[i];
            var realigned_unit_data=realign_spikes(unit_trials.get(unit_id), unit_trial_events.get(unit_id), align_event);
            var rate=get_firing_rate(realigned_unit_data, binwidth, width);
            var unit_min_time=d3.min(rate, function(d){ return d.x; });
            var unit_max_time=d3.max(rate, function(d){ return d.x; });
            if(unit_min_time<min_time)
                min_time=unit_min_time;
            if(unit_max_time>max_time)
                max_time=unit_max_time;
            var unit_max_rate=d3.max(rate, function(d){ return d.y+1 });
            if(unit_max_rate>max_rate)
                max_rate=unit_max_rate;
            rate_data.set(unit_id, rate);

        }

        yScale.domain([0, max_rate +.1*max_rate]);
        yAxis.scale(yScale);
        xScale.domain([min_time, max_time]);
        xAxis.scale(xScale);

        xBinwidth =  width / (rate.length-1);
        var realigned_unit_trials_events=new Map();
        for(var i=0; i<event_types.length; i++)
        {
            var event_type=event_types[i];
            var times=[];
            for(var k=0; k<unit_ids.length; k++)
            {
                var unit_id=unit_ids[k];
                var unit_times=[];
                if(realigned_unit_trials_events.get(unit_id)==null)
                    realigned_unit_trials_events.set(unit_id,realign_events(unit_trial_events.get(unit_id), align_event));
                var realigned_trial_events=realigned_unit_trials_events.get(unit_id);
                for(var j=0; j<realigned_trial_events.length; j++)
                {
                    if(realigned_trial_events[j].name==event_type)
                        unit_times.push(realigned_trial_events[j].t);
                }
                times.push(d3.mean(unit_times));
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

        for(var i=0; i<unit_ids.length; i++)
        {
            var unit_id=unit_ids[i];
            rate_svg.selectAll('#condition-unit-'+unit_id).datum(rate_data.get(unit_id))
                .transition().duration(1000)
                .attr("class", "data-line")
                .attr("d", line);
        }
        rate_svg.selectAll(".text").data(hist).remove();
        rate_svg.select(".y.axis").call(yAxis);
        rate_svg.select(".x.axis").call(xAxis);

    }
}

function drawUnitPopulationFiringRate(unit_id, condition_trials, condition_trial_events, event_types, condition_names)
{
    var scaleFactor=0.5;
    var margin = {top: 30, right: 20, bottom: 40, left: 50}
        , width = scaleFactor*(960 - margin.left - margin.right)
        , height = scaleFactor*(400 - margin.top - margin.bottom);

    var rate_svg = d3.select("#unit-"+unit_id+"-plots").append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var binwidth = parseInt(d3.select("#binwidth").node().value);
    d3.selectAll("#binwidth").on("change.rate.unit."+unit_id, update);

    var align_event = d3.select("#align_event").node().value;
    d3.selectAll("#align_event").on("change.rate.unit."+unit_id, update);
    var rate_data=new Map();
    var min_time=10000;
    var max_time=-10000;
    var max_rate=0;
    for(var i=0; i<condition_ids.length; i++)
    {
        var condition_id=condition_ids[i];
        var realigned_condition_data=realign_spikes(condition_trials.get(condition_id), condition_trial_events.get(condition_id), align_event);
        var rate=get_firing_rate(realigned_condition_data, binwidth, width);
        rate_data.set(condition_id,rate);
        var condition_min_time=d3.min(rate, function(d){ return d.x; });
        var condition_max_time=d3.max(rate, function(d){ return d.x; });
        if(condition_min_time<min_time)
            min_time=condition_min_time;
        if(condition_max_time>max_time)
            max_time=condition_max_time;
        var condition_max_rate=d3.max(rate, function(d){ return d.y+1 });
        if(condition_max_rate>max_rate)
            max_rate=condition_max_rate;
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

    var max_length=d3.max(condition_names, function(d){return d.length});

    for(var i=0; i<condition_ids.length; i++)
    {
        rate_svg.append("path")
            .attr("id", "unit-condition-"+condition_ids[i])
            .datum(rate_data.get(condition_ids[i]))
            .attr("class", "data-line")
            .style("stroke", p(i))
            .attr("d", line);
        rate_svg.append("text")
            .attr("class","legend-label")
            .attr("x",width-max_length*7)
            .attr("y",margin.top+i*20)
            .style("fill", p(i))
            .text(condition_names[i])
            .on("click", function(d){
                document.location.href="/mirrordb/condition/"+d.id+"/";
            });;
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
    var realigned_condition_trials_events=new Map();
    for(var i=0; i<event_types.length; i++)
    {
        var event_type=event_types[i];
        var times=[];
        for(var k=0; k<condition_ids.length; k++)
        {
            var condition_id=condition_ids[k];
            var condition_times=[];
            if(realigned_condition_trials_events.get(condition_id)==null)
                realigned_condition_trials_events.set(condition_id,realign_events(condition_trial_events.get(condition_id), align_event));
            var realigned_trial_events=realigned_condition_trials_events.get(condition_id)
            for(var j=0; j<realigned_trial_events.length; j++)
            {
                if(realigned_trial_events[j].name==event_type)
                    condition_times.push(realigned_trial_events[j].t);
            }
            times.push(d3.mean(condition_times));
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
                    align_all_events(d);
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
        for(var j=0; j<condition_ids.length; j++)
        {
            rate=rate_data.get(condition_ids[j]);
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

    function update(){
        binwidth = parseInt(d3.select("#binwidth").node().value);
        var align_event = d3.select("#align_event").node().value;
        rate_data=new Map();
        var min_time=10000;
        var max_time=-10000;
        var max_rate=0;
        for(var i=0; i<condition_ids.length; i++)
        {
            var condition_id=condition_ids[i];
            var realigned_condition_data=realign_spikes(condition_trials.get(condition_id), condition_trial_events.get(condition_id), align_event);
            var rate=get_firing_rate(realigned_condition_data, binwidth, width);
            var condition_min_time=d3.min(rate, function(d){ return d.x; });
            var condition_max_time=d3.max(rate, function(d){ return d.x; });
            if(condition_min_time<min_time)
                min_time=condition_min_time;
            if(condition_max_time>max_time)
                max_time=condition_max_time;
            var condition_max_rate=d3.max(rate, function(d){ return d.y+1 });
            if(condition_max_rate>max_rate)
                max_rate=condition_max_rate;
            rate_data.set(condition_id, rate);

        }

        yScale.domain([0, max_rate +.1*max_rate]);
        yAxis.scale(yScale);
        xScale.domain([min_time, max_time]);
        xAxis.scale(xScale);

        xBinwidth =  width / (rate.length-1)
        var realigned_condition_trials_events=new Map();
        for(var i=0; i<event_types.length; i++)
        {
            var event_type=event_types[i];
            var times=[];
            for(var k=0; k<condition_ids.length; k++)
            {
                var condition_id=condition_ids[k];
                var condition_times=[];
                if(realigned_condition_trials_events.get(condition_id)==null)
                    realigned_condition_trials_events.set(condition_id,realign_events(condition_trial_events.get(condition_id), align_event));
                var realigned_trial_events=realigned_condition_trials_events.get(condition_id);
                for(var j=0; j<realigned_trial_events.length; j++)
                {
                    if(realigned_trial_events[j].name==event_type)
                        condition_times.push(realigned_trial_events[j].t);
                }
                times.push(d3.mean(condition_times));
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

        for(var i=0; i<condition_ids.length; i++)
        {
            var condition_id=condition_ids[i];
            rate_svg.selectAll('#unit-condition-'+condition_id).datum(rate_data.get(condition_id))
                .transition().duration(1000)
                .attr("class", "data-line")
                .attr("d", line);
        }
        rate_svg.selectAll(".text").data(hist).remove();
        rate_svg.select(".y.axis").call(yAxis);
        rate_svg.select(".x.axis").call(xAxis);

    }
}
