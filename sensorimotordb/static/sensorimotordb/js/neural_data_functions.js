function loadObject(resource_uri)
{
    var obj=null;
    var data = {};
    var args = {
        type: "GET",
        async: false,
        url: resource_uri,
        data: data,
        success: function(data){
            obj=data;
        },
        error: function(data) {
            //alert("Something went wrong!");
        } };
    $.ajax(args);
    return obj;
}


/**
 *
 * @param trials - list of spikes with x=spike time, y=trial number
 * @param trial_events - list of events with t=time, trial=trial number
 * @param event_name
 * @return {Array}
 */
function realign_spikes(trial_spikes, trial_events, event_name)
{
    // List of realigned spikes
    var realigned_spikes=[];

    // Align event for each trial
    var trialAlignEvents=new Map();

    // Iterate through all spikes
    for(var spike_idx=0; spike_idx<trial_spikes.length; spike_idx++)
    {
        // Index of align event
        var align_evt_idx=-1;
        // Get trial ID for this spike
        var trial_id=trial_spikes[spike_idx].y;

        // Get align event index from map if it is already there
        if(trialAlignEvents.has(trial_id))
        {
            align_evt_idx=trialAlignEvents.get(trial_id);
        }
        // Otherwise figure out align event
        else
        {
            // Iterate through all events
            for(var evt_idx=0; evt_idx<trial_events.length; evt_idx++)
            {
                // If this event is for this trial
                if(trial_events[evt_idx].trial==trial_id)
                {
                    // If this is the align event -set align event index and stop looking
                    if(event_name==trial_events[evt_idx].name)
                    {
                        align_evt_idx=evt_idx;
                        break
                    }
                }
            }
            trialAlignEvents.set(trial_id,align_evt_idx)
        }
        if(align_evt_idx>-1)
        {
            // Get align event
            var align_evt=trial_events[align_evt_idx];
            // Push realigned spike time
            realigned_spikes.push({
                x: (trial_spikes[spike_idx].x-align_evt.t)*1000.0,
                y: trial_spikes[spike_idx].y
            });
        }
    }
    return realigned_spikes;
}

function realign_events(trial_events, event_name)
{
    var realigned=[];
    for(var evt_idx=0; evt_idx<trial_events.length; evt_idx++)
    {
        if(trial_events[evt_idx].name==event_name)
        {
            realigned.push({
                t: 0,
                trial: trial_events[evt_idx].trial,
                name: trial_events[evt_idx].name,
                description: trial_events[evt_idx].description
            });
        }
        else
        {
            var start_evt_idx=-1;
            var align_evt_idx=-1;
            for(var other_evt_idx=0; other_evt_idx<trial_events.length; other_evt_idx++)
            {
                if(trial_events[other_evt_idx].trial==trial_events[evt_idx].trial)
                {
                    if(trial_events[other_evt_idx].name=='start')
                        start_evt_idx=other_evt_idx;
                    else if(trial_events[other_evt_idx].name==event_name)
                        align_evt_idx=other_evt_idx;
                }
            }
            if(align_evt_idx<0)
                align_evt_idx=start_evt_idx;
            var align_evt=trial_events[align_evt_idx];
            realigned.push({
                    t: (trial_events[evt_idx].t-align_evt.t)*1000.0,
                    trial: trial_events[evt_idx].trial,
                    name: trial_events[evt_idx].name,
                    description: trial_events[evt_idx].description
            });
        }
    }
    return realigned;
}

function get_standard_firing_rate(trials, bins, bin_width, kernel_width)
{
    var variance=kernel_width/bin_width;
    var window=[];
    for(var i=-2*bin_width; i<2*bin_width+1; i++)
        window.push(Math.exp(-Math.pow(i,2)*(1/(2*Math.pow(variance,2)))));
    var windowSum=d3.sum(window, function(x){return x});
    for(var i=0; i<window.length; i++)
        window[i]=window[i]*(1.0/windowSum);

    var numTrials=d3.max(trials, function(d){ return d.y});

    hist = d3.layout.histogram()
        .bins(bins)
        (trials.map(function(d) {return d.x; }));

    var scaledHist=[];
    for(var j=0; j<hist.length; j++)
        scaledHist.push({
            x: hist[j].x,
            y: hist[j].y/numTrials/(bin_width/1000.0)
        });

    var rate = convolute(scaledHist, window, function(datum){
        return datum.y;
    });
    return rate;
}

function get_firing_rate(trials, bin_width, kernel_width)
{
    var xScale = d3.scale.linear()
        .domain([d3.min(trials, function(d) { return d.x; }), d3.max(trials, function(d) { return d.x; })]);;
    var bins=d3.range(xScale.domain()[0], xScale.domain()[1]+bin_width, bin_width)

    return get_standard_firing_rate(trials, bins, bin_width, kernel_width)
}

function mean_firing_rate(rates, times)
{
    var sqrt_n=Math.sqrt(rates.length);
    var mean_rate=times.map(
        function(d,i){
            var time_rates=rates.map(
                function(e){
                    return e[i].y
                }
            );
            return {
                x: d,
                y: d3.mean(time_rates),
                stderr: rates.length>1 ? d3.deviation(time_rates)/sqrt_n : 0
            }
        }
    );
    return mean_rate;
}



function convolute(data, kernel, accessor){
    var kernel_center = Math.floor(kernel.length/2);
    if(accessor == undefined){
        accessor = function(datum){
            return datum;
        }
    }
    function constrain(i,range){
        if(i<range[0]){
            i=0;
        }
        if(i>range[1]){
            i=range[1];
        }
        return i;
    }
    var convoluted_data = data.map(function(d,i){
        var s = 0;
        for(var k=0; k < kernel.length; k++){
            var index = constrain( ( i + (k-kernel_center) ), [0, data.length-1] );
            s += kernel[k] * accessor(data[index]);
        }
        return {'x': data[i].x, 'y': s};
    });
    return convoluted_data;
}

function normalize_unit_rate(unit_rate, max_rate)
{
    var normRate=[];
    for(var j=0; j<unit_rate.length; j++)
        normRate.push({
            x: unit_rate[j].x,
            y: unit_rate[j].y/max_rate
        });
    return normRate;
}