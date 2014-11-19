$body = $("body");

$(document).ready(function() {
	$("#strains").select2({
		placeholder: 'Select strain/s',
		allowClear: true,
		width: '100%',
		multiple: true,
		query: function(query) {
			var data = { results: [] };
			// the current text being entered into the select2 box
			var current_text = $("#strains").data('select2').search.val();
			$.getJSON('/strains/list', function(d) {
				console.log(d);
				for (var i = 0; i < d.length; i++) {
					data.results.push({id: d[i], text: d[i]});
				}
			query.callback(data);
			});
		}
	});

	/*$("#loci").select2({
		placeholder: 'Select Loci',
		width: '100%',
		multiple: true,
		query: function(query) {
			var data = { results: [] };
			// the current text being entered into the select2 box
			var current_text = $("#loci").data('select2').search.val();
			$.getJSON('_get_distinct_loci', {
				text : current_text
			}, function(d) {
				for (var i = 0; i < d.length; i++) {
					if (d[i].LocusTag == null)
						data.results.push( {id: "None", text: "None" });
					else
						data.results.push( {id: d[i].LocusTag, text: d[i].LocusTag} );
				}
			query.callback(data);
			});
		}
	});

    $("#keyword_submit").click(function() {
        var selected = [];
        $("#checkboxes input:checked").each(function() {
            selected.push($(this).attr('id'));
        });
        if (!selected.length) {
		    $("#keyword_error").show();
        } else {
            $("#keyword_error").hide();
            console.log(selected);
            $("#loading-snp-keyword").show();
            $.getJSON('_get_details_by_product', {
                products : JSON.stringify(selected)
            }, function(d) {
                draw_product_heatmap(d);
                $("#loading-snp-keyword").hide();
            });
        }
    }); */

	/* Need to set a delay here, after the first keyup maybe wait half a second? */
	/* Update the search table results whenever new data is typed into the box */
	$("#keyword").keyup (function(e) {
        $("#keyword_error").hide();
		if (e.currentTarget.value) {
			var results = []
			$.getJSON('_get_locus_by_keyword', {
				keyword: e.currentTarget.value	
			}, function(d) {
				for (var i = 0; i < d.length; i++) {
					results.push( d[i].Product );
				}			
				html = generate_product_table(results, e.currentTarget.value);
				$("#keyword_table").html(html);
			});	
		} else {
			$("#keyword_table").html("");
		}	
	});

    // Generate graph when user selects strain
	$("#strains").on("change", function(e) {
		var strain_selections = ( $("#strains").select2("val") );
		var loci_selections = "[]";
		$("#loading-snp").show();

        selected_strain = strain_selections.slice(-1)[0]; // Last element, last selected strain
        console.log(strain_selections.slice(-1)[0]);
        $.getJSON('/strains/stats', {
            sid: selected_strain,
		}, function(d) {
			write_raw_strain_info(d);
		});

		//$.getJSON('_get_snp_locus_details', {
        $.getJSON('/variants/list', {
			sid: selected_strain,
		}, function(d) {
			$("#raw-strain-info").show();
            draw_snp_bar_chart(strain_selections[0], d);
			$("#loading-snp").hide();
		});
	});
});

function write_raw_strain_info(strains) {
	if (strains.length < 1)
		return 0;

	html = '<table class="table"> <tr>';
	// Headers
	html += '<th> StrainID </th>';
	html += '<th> Total SNPs </th>';
	html += '<th> Substitutions </th>';
	html += '<th> Insertions </th>';
	html += '<th> Deletions </th>';
	html += '</tr>';
	
	for (var i = 0; i < strains.length; i++) {
		html += '<tr>';
		html += '<td>' + strains[i].StrainID + '</td>';
		html += '<td>' + strains[i].total + '</td>';
		html += '<td>' + strains[i].substitution + '</td>';
		html += '<td>' + strains[i].insertion + '</td>';
		html += '<td>' + strains[i].deletion + '</td>';
		html += '</tr>';
	}
	html += '</table>';
	$("#raw-strain-info-table").html(html);
}

/* Creates a selection box table for all the product data */
function generate_product_table(data, searchQuery) {
	if (data.length < 1) {
		return "No matches found.";
	}
	html = '<div class="checkbox" value="" onclick="toggle_selectall(this);"><label><input type="checkbox" id="select_all"/>Select All</label></div>';
    html += '<div id="checkboxes">';

	for (var i = 0; i < data.length; i++) {
		/* Generate the product string with the current search query underlined */
		var index = data[i].indexOf(searchQuery)
		dataUnderlined = data[i].substring(0, index);
		dataUnderlined += '<u>' + data[i].substring(index, index + searchQuery.length) + '</u>';
		dataUnderlined += data[i].substring(index + searchQuery.length, data[i].length);
		html += '<div class="checkbox" onclick="toggle_select(this);" name="' + data[i] + '"><label><input type="checkbox" name="products" id="' + data[i] + '" value=""/>' + dataUnderlined + '</label></div>';
	}
    html += '</div>';
	return html;
}

function toggle_selectall(source) {
    selectAll = document.getElementById('select_all');
    if (!selectAll.checked) 
        selectAll.checked = true;
    else
        selectAll.checked = false;
    //source.setAttribute('checked', source.checked);
	checkboxes = document.getElementsByName('products');
	for (var i = 0; i < checkboxes.length; i++) {
		checkboxes[i].checked = selectAll.checked;
	}
}

function toggle_select(source) {
    /* TODO fix the fact that select boxes are not working
    for some strange reason */
}

/* Generates the HTML for SNP tables to display raw data about a strain */
function generate_snp_tables(data) {
	var table_html = '';
	for (var i = 0; i < data.length; i++) {
	}
}

$(document).ajaxStart(function() {
    $body.addClass("loading");
});
