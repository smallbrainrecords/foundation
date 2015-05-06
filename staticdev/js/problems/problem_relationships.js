function generateProblemRelationshipsHtml(problemJson) {
    var problemRelationshipsHtml = '';
           select = "<ul style='background:gray'>";
            for (var j = 0; j < data.length; j++) {
                if (data[j]['problem_name'] != problem[
                    'problem_name']) {
                    console.log(problem['effected_by'][data[j][
                        'problem_id'
                    ].toString()]);
                    //console.log("problem['effected_by']['"+data[j]['problem_id'].toString()+"'])";
                    if (problem['effected_by'][data[j]['problem_id']
                        .toString()
                    ] == true) {
                        var checked = ' checked ';
                    } else {
                        var checked = '';
                    }
                    select += '<li>';
                    // 'target': target, 'id': $(this).attr('id'), 'value': $(this).is(':checked'), 'attr': $(this).attr('attr')
                    select += data[j]['problem_name'] +
                        '<input type="checkbox" ' + checked +
                        ' target="' + data[j]['problem_id'] + '" ';
                    select += 'id="' + problem['problem_id'] +
                        '" attr="effected_by" />';
                    select += '</li>';
                }
            }
            select += "</ul>&darr;<br/>";
            select += problem['problem_name'] +
                "<br/>&darr;<br/><ul style='background:gray'>";
            for (var j = 0; j < data.length; j++) {
                if (data[j]['problem_name'] != problem[
                    'problem_name']) {
                    console.log(problem['affects'][data[j][
                        'problem_id'
                    ].toString()]);
                    //console.log("problem['effected_by']['"+data[j]['problem_id'].toString()+"'])";
                    if (problem['affects'][data[j]['problem_id'].toString()] ==
                        true) {
                        var checked = ' checked ';
                    } else {
                        var checked = '';
                    }
                    select += '<li>';
                    select += data[j]['problem_name'] +
                        '<input type="checkbox" ' + checked +
                        ' target="' + data[j]['problem_id'] + '" ';
                    select += 'id="' + problem['problem_id'] +
                        '" attr="affects" />';
                    select += '</li>';
                }
            }
            select += "</ul>";
            affects = '';
            for (var j = 0; j < problem['affects'].length; j++) {
                var a = problem['affects'][j];
                affects += '<input type="button" value="' + a[
                    'problem_name'] + '" ';
                affects +=
                    'class="show_problem" id="control_display_for_problem_' +
                    a['problem_id'] + '" ';
                affects += 'target="problem_data_' + a['problem_id'] +
                    '" ';
                affects += 'problem="' + a['problem_id'] + '" />';
            }
            relationships +=
                '<li><strong>Start date:</strong> <input type="text" id="problem_start_date_' +
                problem['problem_id'] + '" ';
            relationships += 'value="' + problem['start_date'] +
                '" />';
            relationships +=
                '<input type="button" value="Submit new date" parent="' +
                problem['problem_id'] + '" ';
            relationships += 'target="problem_start_date_' +
                problem['problem_id'] +
                '" object_type="problem_start_date" class="submit_data"/></li>';
            relationships += '<li>' + select + '</li>';
    return problemRelationshipsHtml;
}
