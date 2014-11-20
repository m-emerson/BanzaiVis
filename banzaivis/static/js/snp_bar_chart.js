/* Use d3.js to draw the variance stacked bar chart */
function draw_snp_bar_chart(strain, data, coverage) {
    var lastPos;
    
    var selected = [];
    draw_select_box(data['layers'][0].values);
    var main_margin = {top: 20, right: 20, bottom: 120, left: 40},
        main_width = 900 - main_margin.left - main_margin.right,
        main_height = 600 - main_margin.top - main_margin.bottom;

    var mini_margin = {top: 540, right: 80, bottom: 20, left: 40},
        mini_height = 600 - mini_margin.top - mini_margin.bottom;

    /* Stack layout for stacked bar chart */
    var layers = d3.layout.stack()
        .values(function(d) { return d.values; })(data['layers']);

    /* Keep track of the index of each locus tag */
    var loci_indexes = []
    for (var i in data['layers'][0].values) {
        loci_indexes[data['layers'][0].values[i]['x']] = i;
    }
   
    var maxValue = Math.max.apply(Math,data['coverage'].map(function(d){ return d.coverage; }));

    // Coverage: 0:red 1:white max:green
    var c = d3.scale.linear()
        .domain([0, 1, maxValue])
        .range(["red", "white", "green"]);

    var xMax = data['layers'][0].values.length;
    var yStackMax = d3.max(layers, function(layer) {
        return d3.max(layer.values, function(d) { return d.y0 + d.y; });
    });

    var color = d3.scale.ordinal()
        .range(["#8A0829", "#0B0B61", "#2E2E2E", "#61380B"]);

    var main_x0 = d3.scale.ordinal()
        .domain(layers[0].values.map(function(d) { return d.x; }))
        .rangeBands([0, main_width], .1);

    var mini_x0 = d3.scale.ordinal()
        .domain(layers[0].values.map(function(d) { return d.x; }))
        .rangeBands([0, main_width], .1);

    var main_xZoom = d3.scale.linear()
        .range([0, main_width], .1)
        .domain([0, main_width]);

    var main_y = d3.scale.linear()
        .domain([0, yStackMax])
        .rangeRound([main_height, 0]);

    var mini_y = d3.scale.linear()
        .domain([0, yStackMax])
        .rangeRound([mini_height, 0]);

    var main_xAxis = d3.svg.axis()
        .scale(main_x0)
        .orient("bottom")
        .tickFormat(function(d) { return ''; });

    var mini_xAxis = d3.svg.axis()
        .scale(mini_x0)
        .orient("bottom")
        .tickFormat(function(d) { return ''; }); // No x-axis ticks on mini graph

    var main_yAxis = d3.svg.axis()
        .scale(main_y)
        .orient("left");

    var svg = d3.select("#graph").append("svg")
        .attr("width", main_width + main_margin.left + main_margin.right)
        .attr("height", main_height + main_margin.top + main_margin.bottom);

    var main = svg.append("g")
        .attr("transform", "translate(" + main_margin.left + "," + main_margin.top + ")");

    var mini = svg.append("g")
        .attr("transform", "translate(" + mini_margin.left + "," + mini_margin.top + ")");

    var brush = d3.svg.brush()
        .x(mini_x0)
        .on("brushend", brushed);

    // Add the Y axis
    main.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(0,0)")
        .call(main_yAxis)
    .style("fill", "black")
    .style("stroke", "black");

    // Layer for stacked bar chart
    var snpClass = main.selectAll(".snpClass")
        .data(layers)
        .enter().append("g")
        .attr("class", "layer")
        .style("fill", function(d) { return color(d.class); });

    // Add the X axis
    snpClass.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + main_height + ")")
        .call(main_xAxis)
        .selectAll("text")
            .style("text-anchor", "end")
            .style("fill", "black")
            .style("font-size", "11px")
            .attr("dy", "-.5em")
            .attr("transform", function(d) {
                //return "translate(0, 40)rotate(-90)";
                return "translate(0, 40)rotate(-90)";
            });

    // Stacked bar chart
    var rect = snpClass.selectAll("rect")
        .data(function(d) { return d.values })
        .enter().append("rect")
        .attr("x", function(d) { return main_x0(d.x) })
        .attr("y", main_height)
        .attr("width", main_x0.rangeBand())
        .attr("height", 0)
        .on("click", function(d) {
            d3.event.stopPropagation();
            bar_select(d.x);
        });

    // Coverage bar
    var coverage = snpClass.selectAll(".coverage")
        .data(data['coverage'])
        .enter().append("rect")
        .attr("x", function(d) { return main_x0(d.x); })
        .attr("y", main_height + 5)
        .attr("width", main_x0.rangeBand())
        .attr("height", 10)
        .style("fill", function(d, i) { return c(d.coverage); });

    // Clip dimensions
    var clip = snpClass.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("id", "clip-rect")
        .attr("x", 0) 
        .attr("y", 0)
        .attr("width", main_width)
        .attr("height", main_height + mini_margin.top + main_margin.top);

    // Clip graph
    snpClass.attr("clip-path", "url(#clip)");

    // Set the positions of each stacked bar
    rect.transition()
        .delay(10)
        .attr("y", function(d) { if (isNaN(main_y(d.y0 + d.y))) { console.log(d.y0); console.log(d.y); console.log(d.x); } return main_y(d.y0 + d.y); })
        .attr("height", function(d) { return main_y(d.y0) - main_y(d.y0 + d.y); });

    // Add the mini x axis
    mini.append("g")
        .attr("class", "x axis mini_axis")
        .attr("transform", "translate(0," + mini_height + ")")
        .call(mini_xAxis);

    // Add brush element to mini graph
    mini.append("g")
        .attr("class", "x brush")
        .call(brush)
        .style("fill-opacity", ".125")
        .selectAll("rect")
        .attr("y", 0)
        .attr("height", mini_height + 5); 

    // Create the mini stacked bars
    var miniSnpClass = mini.selectAll(".miniSnpClass")
        .data(layers)
        .enter().append("g")
        .attr("class", "layer")
        .style("fill", function(d) { return color(d.class); });

    var mini_rect = miniSnpClass.selectAll("mini_rect")
        .data(function(d) { return d.values; })
        .enter().append("rect")
        .attr("x", function(d) { return mini_x0(d.x) })
        .attr("y", mini_height)
        .attr("width", mini_x0.rangeBand())
        .attr("height", 0);

    mini_rect.transition()
        .delay(10)
        .attr("y", function(d) { return mini_y(d.y0 + d.y); })
        .attr("height", function(d) { return mini_y(d.y0) - mini_y(d.y0 + d.y); });

    // Legend for stacked bars
    var legend = svg.selectAll(".legend")
        .data(color.domain().slice().reverse())
        .enter().append("g")
            .attr("class", "legend")
            .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });
    
    legend.append("rect")
        .attr("x", main_width + main_margin.right)
        .attr("width", 15)
        .attr("height", 15)
        .style("fill", color)
        .on("mouseout", function(d) { snpClass.style("fill-opacity", "1"); snpClass.selectAll("text").remove(); });

    legend.append("text")
        .attr("x", main_width + main_margin.right - 15)
        .attr("y", 7.5)
        .attr("dy", ".35em")
        .style("text-anchor", "end")
        .text(function(d) { return d; });
    
    // Load graph with an initial brush selection 
    brush.extent([0, 10]);
    svg.select(".brush").call(brush)
                        .call(brushed);
   
    function brushed() {
        var originalRange = main_xZoom.range();
        main_xZoom.domain(brush.empty() ? 
                            originalRange: 
                            brush.extent() );
        main_x0.rangeBands( [
            main_xZoom(originalRange[0]),
            main_xZoom(originalRange[1])
            ], 0.1);

        p = brush.extent();

        brushrange = p[1] - p[0];

        // Draw labels only if brush dimensions are less than 15
        if (brushrange == 0 || brushrange > 15) 
            main_xAxis.tickFormat(function(d) { return ''; });
        else
            main_xAxis.tickFormat(function(d) { return d; }); 

        // Redraw bars, x axis and reclip graph
        rect
            .attr("width", function (d) {
                return main_x0.rangeBand();
            })
            .attr("x", function (d) {
                return main_x0(d.x);
            }); 

        coverage
            .attr("width", function (d) {
                return main_x0.rangeBand();
            })
            .attr("x", function(d) {
                return main_x0(d.x);
            });
 
        main.select("g.x.axis").call(main_xAxis)
            .selectAll("text")
            .attr("transform", function(d) {
                return "translate(" + -(main_x0.rangeBand()) + ", 40)rotate(-90)";
            });

        snpClass.attr("clip-path", "url(#clip)");
    } 

    /*
     * Highlights a bar if it has been selected, and loads raw variance information
     */
    function bar_select(locus) {
        var notSelected = rect.filter(function(b) {
            return b.x != locus;
        });
    
        var selected = rect.filter(function(b) {
            return b.x == locus;
        });

        notSelected.style("fill-opacity", "0.5");
        selected.style("fill-opacity", "1");
        
        $("#locus_load").show();
        $.getJSON('/variants/locus', {
            locus: locus, sid: strain
        }, function(r) {
            draw_sequence(r.snps, r.seq_info[0]);
            if (r.snps.length > 0)
                write_table(r.snps);
            else
                $("#table").html("");
            $("#locus_load").hide();
        });

    }

    function highlight_class(data) {
        notSelected = snpClass.filter(function(d) {
            return (d.class != data) 
        });
      
        selected = snpClass.filter(function(d) {
            return d.class == data
        }); 

        // Add frequency label for selected class
        selected.selectAll("labels")
            .data(function(d) { return d.values })
            .enter()
            .append("text")
            .style("font-size", "8px")
            .style("fill", "black")
            .attr("text-anchor", "start")
            .attr("x", function(d) {
                return main_x0(d.x) + (main_x0.rangeBand() / 2);
            })
            .attr("y", function(d) {
                if (d.y != 0)
                    return main_y(d.y0);  
            }) 
            .style("text-anchor", "middle")
            .text(function(d) {
                return Number((d.y).toFixed(3));
            });

        // Highlight selected class only
        notSelected.style("fill-opacity", "0.5");
    }

    /*
     * Generates and sets the html to display raw variance information
     */
    function write_table(data) {
        headings = ["StrainID", "Position", "RefBase", "ChangeBase", "ChangeAA", "Class", "SubClass"];
        html = "<h2>" + data[0]['LocusTag'] + " : " + data[0]['Product'] + "</h2>";
        html += "<table class='table'>";
        html += "<thead id='headings'><tr>";
        for (var h in headings) {
            html += "<th id='" + headings[h] + "'><a>" + headings[h] + "</a></th>";
        }
        html += "</tr></thead>";
        html += "<tbody>"
        for (var d in data) {
            html += "<tr>";
            for (var h in headings) {
                html += "<td>" + data[d][headings[h]] + "</td>";
            }
        }
        html += "</table>";
        $("#table").html(html)
    }

    /*
     * Generates a select box with the avaialble locus information
     * Sets the behavior to pan visualisation when an option is selected
     * Uses select2 for easy searches
     */
    function draw_select_box(data) {
        // Select box here
        var select_contents = "";
        for (var d in data) {
            if (data[d].x != null) {
                select_contents += "<option value='" + data[d].x + "'>" + data[d].x + "</option>";
            }
        }
        var jump = "Jump to: <select id='jump'>" + select_contents + "</select>";
        var html = jump;
        $("#header").html(html);
        $("#jump").select2({ width: '50%' });
        $("#jump").change(function() {
            var selected_jump = $("#jump>option:selected").html();
            var index = loci_indexes[selected_jump];
            var loci_location = loci_indexes[selected_jump] * mini_x0.rangeBand();

            from_val = mini_x0.range()[index] - 5;
            to_val = mini_x0.range()[index] + 5;

            /* TODO: centre and select the correct band */
            brush.extent([from_val, to_val]);
            svg.select(".brush").call(brush)
                                .call(brushed);

            bar_select(selected_jump);
        });
    }
}


/*
* Uses bio.js sequence to display the raw sequence information
* Uses raw variance information to regenerate new sequence with snps & indels 
* included and displayed
*/
function draw_sequence(snps, seq_info) {
    $('#seq_info').html("");
    var annotations = [];
    var highlights = [];

    var highlight;
    var newSequence = "";

    offset = 0;
    snpid = 0;

    substitutions = 0;

    // Modify the reference sequence with reported SNPs
    for (var i=0; i < seq_info['sequence'].length; i++) {
        if (snpid < snps.length) {
            if (i == snps[snpid].CDSBaseNum) {
                if (snps[snpid].Class == "substitution") {
                    newSequence += snps[snpid].ChangeBase;
                    if (snps[snpid].SubClass == "synonymous")
                        highlight = "blue";
                    else
                        highlight = "red";
                    highlights.push( {start: snps[snpid].CDSBaseNum + 1 + offset,
                        end: snps[snpid].CDSBaseNum + 1 + offset,
                        color: highlight,
                    });
                } else if (snps[snpid].Class == "insertion") {
                    newSequence += snps[snpid].ChangeBase;
                    highlights.push( {start: snps[snpid].CDSBaseNum + 1 + offset,
                        end: snps[snpid].CDSBaseNum + snps[snpid].ChangeBase.length + offset,
                        color: "black",
                        background: "yellow",
                    });
                    offset += snps[snpid].ChangeBase.length;
                } else if (snps[snpid].Class == "deletion") {
                    offset -= snps[snpid].RefBase.length; 
                }
                snpid++;
            } else {
                newSequence += seq_info['sequence'].charAt(i);
            }
        }
    }
  
    // Use Bio.js to display the sequence
    var locusSequence = new Biojs.Sequence({
        sequence: newSequence,
        target: "seq_info",
        format: 'CODATA',
        id : seq_info['locus_tag'] + ' - ' + seq_info['product'],
        highlights : highlights
    });
}
