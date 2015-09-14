var bisectTime = d3.bisector(function(d) { return d.x; }).left;
var p=d3.scale.category10();

function align_all_events(align_to)
{
    d3.select("#align_event").node().value= align_to;
    func=d3.select('#align_event').on("change.rate.population.unit-"+unit_id);
    func();
    for(var j=0; j<condition_ids.length; j++)
    {
        func=d3.select("#align_event").on("change.raster.condition-"+condition_ids[j]+"-plots");
        func();
        func=d3.select('#align_event').on("change.histo.condition-"+condition_ids[j]+"-plots");
        func();
        func=d3.select('#align_event').on("change.rate.condition-"+condition_ids[j]+"-plots");
        func();
    }
}

