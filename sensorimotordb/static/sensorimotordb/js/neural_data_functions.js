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


function realign_spikes(trials, trial_events, event_name)
{
    var realigned=[];
    for(var i=0; i<trials.length; i++)
    {
        var event_time=0;
        for(var j=0; j<trial_events.length; j++)
        {
            if(trial_events[j].trial==trials[i].y && trial_events[j].name==event_name)
            {
                event_time=trial_events[j].t;
                break;
            }
        }
        realigned.push({
            x: (trials[i].x-event_time)*1000.0,
            y: trials[i].y
        })
    }
    return realigned;
}

function realign_events(trial_events, event_name)
{
    var realigned=[];
    for(var i=0; i<trial_events.length; i++)
    {
        if(trial_events[i].name==event_name)
        {
            realigned.push({
                t: 0,
                trial: trial_events[i].trial,
                name: trial_events[i].name,
                description: trial_events[i].description
            });
        }
        else
        {
            for(var j=0; j<trial_events.length; j++)
            {
                if(trial_events[j].trial==trial_events[i].trial && trial_events[j].name==event_name)
                {
                    realigned.push({
                        t: (trial_events[i].t-trial_events[j].t)*1000.0,
                        trial: trial_events[i].trial,
                        name: trial_events[i].name,
                        description: trial_events[i].description
                    });
                }
            }
        }
    }
    return realigned;
}

function get_firing_rate(trials, bin_width, width)
{
    var window=[];
    for(var i=-2*bin_width; i<2*bin_width+1; i++)
        window.push(Math.exp(-Math.pow(i,2)*(1/(2*Math.pow(bin_width,2)))));
    var windowSum=d3.sum(window, function(x){return x});
    for(var i=0; i<window.length; i++)
        window[i]=window[i]*(1.0/windowSum);

    var xScale = d3.scale.linear()
        .range([0, width])
        .domain([d3.min(trials, function(d) { return d.x; }), d3.max(trials, function(d) { return d.x; })]);;

    var numTrials=d3.max(trials, function(d){ return d.y});

    hist = d3.layout.histogram()
        .bins(d3.range(xScale.domain()[0], xScale.domain()[1]+bin_width, bin_width))
        (trials.map(function(d) {return d.x; }));

    var scaledHist=[];
    for(var j=0; j<hist.length; j++)
        scaledHist.push({
            x: hist[j].x,
            y: hist[j].y/numTrials/(bin_width/1000.0)
        });

    var smoothed = convolute(scaledHist, window, function(datum){
        return datum.y;
    });
    var rate=[];
    for(var j=0; j<hist.length; j++)
    {
        rate.push({
            x: hist[j].x,
            y: smoothed[j]
        })
    }
    return rate;
}

function convolute(data, kernel, accessor){
    var kernel_center = Math.floor(kernel.length/2);
    var left_size = kernel_center;
    var right_size = kernel.length - (kernel_center-1);
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
        return s;
    });
    return convoluted_data;
}
