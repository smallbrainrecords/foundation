/*
* problems are health issues that are managed through its sub-elements 
* a patient may have zero or many problems.
* problem relationships are how one problem affects another problem
* guidelines are a set of statements used to guide the management of a problem
* images are media files that are associated with a problem
* goals are tasks that are managed over time to create a desired change
* todos are tasks that are done at a particular point in time
* notes are the free text that describe and problem
* status are functional elements of a problem authenticated, controlled, and active
*/

/*
* status: line 126
* notes: line 291
* goals: line 171
* todos: 258
* images: 373
* relationships: line 113
* guidelines: line 157
* history
*/
function updateData() {
    $.get('/get_problems/{{ patient.id }}/', {
        'tracking_id': tracking_id
    }, function(data) {
        var raw_data = data;
        // this is debugging info for developing the syncing of patient pages on multiple devices among multiple users
        $('#viewers').text(JSON.stringify(data.viewers));
        $('#viewers').append(JSON.stringify(data.view_status));
        window.concept_ids = data.concept_ids;
        data = data.problems['is_active'];
        window.problems = data.problems;
        $('#problems').html('');
        for (var i = 0; i < data.length; i++) {
            var problem = data[i];
            relationships = '<ul>';
            var select =
                '<select class="problem_parent submit_data" id="change_problem_parent_' +
                problem['problem_id'] + '" ';
            select += 'target="change_problem_parent_' + problem[
                    'problem_id'] +
                '" object_type="problem_parent" parentlabel="problem &quot;' +
                problem['problem_name'] + '&quot;" parent="' +
                problem['problem_id'] + '">';
            select += '<option value="none">none</option>';
            for (var j = 0; j < data.length; j++) {
                if (data[j]['problem_name'] != problem[
                    'problem_name']) {
                    selected = '';
                    if (data[j]['problem_id'] == problem[
                        'effected_by']) {
                        selected = ' selected';
                    }
                    select += '<option value="' + data[j][
                        'problem_id'
                    ] + '"' + selected + '>';
                    select += data[j]['problem_name'] + '</option>';
                }
            }
            select += '</select>';
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
            //relationships += '<li><strong>Affects:</strong> '+affects+'</li></ul>';
            status = '';
            if (problem['is_controlled'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status +=
                '<label><input type="checkbox" attr="is_controlled" target="problem" id="' +
                problem['problem_id'] + '" ' + checked + '/>';
            status += 'Is controlled</label> &nbsp&nbsp&nbsp&nbsp';
            if (problem['is_authenticated'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status +=
                '<label><input class="status" attr="authenticated" target="problem" id="' +
                problem['problem_id'] + '" ';
            status += 'type="checkbox" ' + checked +
                '/> Is authenticated</label>&nbsp&nbsp&nbsp&nbsp';
            if (problem['is_active'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status +=
                '<label><input type="checkbox" attr="is_active" target="problem" id="' +
                problem['problem_id'] + '" ' + checked +
                '/></label> ';
            status += 'Is active';
            status += '</ul>';
            guidelines = '<ul>';
            for (var j = 0; j < problem['guidelines'].length; j++) {
                guidelines += '<li>' + problem['guidelines'][j][
                    'guideline'
                ];
                guidelines += ' <a href="' + problem['guidelines'][
                    j
                ]['reference_url'] + '">';
                guidelines += problem['guidelines'][j][
                    'reference_url'
                ] + '</a></li>';
            }
            guidelines += '</ul>';
            // Goals: A problem may have zero to many associated with it.  Goals are a way for a patient to define and manage activities that they believe will be of value to them as an individual.  Goals are displayed with the red/green control state.  The goals that have not been set to 'accomplished' are displayed in the problem they are related to.  The note associated with a goal is to describe the motivation for adding that goal.  A GOAL DOES NOT HAVE TO BE ASSOCIATED WITH A PROBLEM.
            goals = '<ul id="goals_' + problem['problem_id'] +
                '" title="goal_' + problem['problem_id'] + '">';
            goals +=
                '<li><strong>Add:</strong> <input type="text" id="goal_input_' +
                problem['problem_id'] + '" />';
            goals +=
                '<input type="button" value="Submit" parentlabel="problem &quot;' +
                problem['problem_name'] + '&quot;" parent="' +
                problem['problem_id'] + '" ';
            goals += 'target="goal_input_' + problem['problem_id'] +
                '" object_type="goal" class="submit_data" /></li>';
            for (var j = 0; j < problem['goals'].length; j++) {
                if (problem['goals'][j]['accomplished'] == true) {
                    checked = ' checked ';
                } else {
                    checked = '';
                }
                if (problem['goals'][j]['is_controlled'] == true) {
                    is_controlled_checked = ' checked ';
                } else {
                    is_controlled_checked = '';
                }
                notes = '<div id="goal_notes_' + problem['goals'][j]
                    ['id'] + '" class="goal_notes">';
                notes += '<strong>Start date:</strong> ' + problem[
                    'goals'][j]['start_date'];
                notes +=
                    '<br/><label><input type="checkbox" aswhat="accomplished" target="goal" attr="goal" label="' +
                    problem['goals'][j]['goal'] + '(for probelm ' +
                    problem['problem_name'] + ')" id="' + problem[
                        'goals'][j]['id'] + '" ' + checked +
                    '/></label> ';
                notes +=
                    '<strong>Is accomplished</strong><br/><input type="checkbox" target="goal" attr="goal_is_controlled" ';
                notes += 'id="' + problem['goals'][j]['id'] +
                    '" aswhat="controlled" label="' + problem[
                        'goals'][j]['goal'] + ' (for probelm ' +
                    problem['problem_name'] + ')" ' +
                    is_controlled_checked + '/> ';
                notes +=
                    '<strong>Currently succeeding</strong><br/><table id="note_' +
                    problem['problem_id'] + '">';
                var role =
                    "{% if user_role == 'admin' %}physician{% else %}{{ user_role }}{% endif %}";
                current_physician_note = '';
                if (problem['goals'][j]['notes'].length > 0) {
                    current_physician_note = problem['goals'][j][
                        'notes'
                    ][0]['note'];
                    console.log(current_physician_note);
                    current_physician_note =
                        '<strong>Motivation for setting this goal:</strong><textarea id="note_input_for_goal_' +
                        problem['goals'][j]['id'] + '" value="' +
                        current_physician_note + '">' +
                        current_physician_note +
                        '</textarea><input type="button" value="Submit" parent="' +
                        problem['goals'][j]['id'] +
                        '" target="note_input_for_goal_' + problem[
                            'goals'][j]['id'] + '" label="' +
                        problem['goals'][j]['goal'] +
                        '(for probelm ' + problem['problem_name'] +
                        ')" object_type="note_for_goal" class="submit_data" />';
                } else {
                    current_physician_note =
                        '<strong>Motivation for setting this goal:</strong><textarea id="note_input_for_goal_' +
                        problem['goals'][j]['id'] + '" value="' +
                        current_physician_note +
                        '" /><input type="button" value="Submit" parent="' +
                        problem['goals'][j]['id'] +
                        '" target="note_input_for_goal_' + problem[
                            'goals'][j]['id'] + '" label="' +
                        problem['goals'][j]['goal'] +
                        '(for probelm ' + problem['problem_name'] +
                        ')" object_type="note_for_goal" class="submit_data" />';
                }
                notes += current_physician_note;
                notes += '</table></div>';
                goals += '<li id="goal_' + problem['goals'][j]['id'] +
                    '" class="' + problem['goals'][j][
                        'is_controlled'
                    ] + '">' + problem['goals'][j]['goal'] +
                    '<input type="button" class="show_goal" value="Show goal" target="goal_notes_' +
                    problem['goals'][j]['id'] + '" goal="' +
                    problem['goals'][j]['id'] + '" />' + notes +
                    '</li>';
            }
            goals += '</ul>';
            todos = '<ul id="todo_' + problem['problem_id'] + '">';
            todos +=
                '<li><strong>Add:</strong> <input type="text" id="todo_input_' +
                problem['problem_id'] +
                '" /><input type="button" value="Submit" parent="' +
                problem['problem_id'] + '" target="todo_input_' +
                problem['problem_id'] +
                '" parentlabel="problem &quot;' + problem[
                    'problem_name'] +
                '&quot;" object_type="todo" class="submit_data" /></li>';
            for (var j = 0; j < problem['todos'].length; j++) {
                console.log(problem['todos'][j]['accomplished']);
                console.log(problem['todos'][j]['accomplished'] ==
                    true);
                if (problem['todos'][j]['accomplished'] == true) {
                    checked = ' checked ';
                } else {
                    checked = '';
                }
                //todos += '<li><input type="checkbox" id="'+problem['todos'][j]['todo_id']+'" attr="accomplished" target="todo" content="'+problem['todos'][j]['todo']+' (for problem '+problem['problem_name']+')" id="'+problem['todos'][j]['id']+'" '+checked+'/>'+problem['todos'][j]['todo']+'</li>';
                todos += '<li><input content="' + problem['todos'][
                        j
                    ]['todo'] + ' (for problem ' + problem[
                        'problem_name'] + ')" id="' + problem[
                        'todos'][j]['id'] +
                    '" h="h" type="checkbox" ' + checked +
                    ' target="todo" attr="accomplished" id="' +
                    problem['todos'][j]['todo_id'] + '" /> ' +
                    problem['todos'][j]['todo'] + '</li>';
            }
            todos += '</ul>';
            // Notes: both the physian and the patient have their own note space for documenting the problem.  A physician can only edit the physician's note, and a physician can ONLY view the patient's note.  A patient can ONLY view the physician's note, and a patient can edit a patient note.  The most recent version of a note is read from database each time the problem is visited.
            //notes = '<table id="note_'+problem['problem_id']+'">';
            var role =
                "{% if user_role == 'admin' %}physician{% else %}{{ user_role }}{% endif %}";
            current_physician_note = '';
            if (problem['notes']['by_physician'].length > 0) {
                current_physician_note = problem['notes'][
                    'by_physician'
                ][0]['note'];
                if (role == 'physician') {
                    current_physician_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_physician_note + '">' +
                        current_physician_note +
                        '</textarea><input type="button" value="Submit" parentlabel="problem &quot;' +
                        problem['problem_name'] +
                        '&quot;" parent="' + problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            } else {
                if (role == 'physician') {
                    current_physician_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_physician_note + '">' +
                        current_physician_note +
                        '</textarea><input type="button" value="Submit" parentlabel="problem &quot;' +
                        problem['problem_name'] +
                        '&quot;" parent="' + problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            }
            current_patient_note = '';
            if (problem['notes']['by_patient'].length > 0) {
                current_patient_note = problem['notes'][
                    'by_patient'
                ][0]['note'];
                if (role == 'patient') {
                    current_patient_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_patient_note + '">' +
                        current_patient_note +
                        '</textarea><input type="button" value="Submit" parentlabel="problem &quot;' +
                        problem['problem_name'] +
                        '&quot;" parent="' + problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            } else {
                if (role == 'patient') {
                    current_patient_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_patient_note + '">' +
                        current_patient_note +
                        '</textarea><input type="button" value="Submit" parentlabel="problem &quot;' +
                        problem['problem_name'] +
                        '&quot;" parent="' + problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            }
            // cols="50"    notes += '<tr><td colspan="2"><strong>Add:</strong> <textarea id="note_input_'+problem['problem_id']+'" value="'+current_physician_note+'">'+current_physician_note+'</textarea><input type="button" value="Submit" parent="'+problem['problem_id']+'" target="note_input_'+problem['problem_id']+'" object_type="note" class="submit_data" /></td></tr>';
            // notes += '<div>By physician<div>By patient</th></tr>';
            notes = '<div><strong>Physician note:</strong><br/>' +
                current_physician_note + '</div>'
            notes += '<div><strong>Patient note:</strong><br/>' +
                current_patient_note + '</div>';
            //for (var j=0;j<problem['notes'].length;j++) {
            //    notes += '<tr><td colspan="5">(by '+problem['notes'][j]['by']+') '+problem['notes'][j]['note']+'</td></tr>';
            //}
            //notes += '</table>';
            var image_form =
                '<form action="/upload_image_to_problem/' + problem[
                    'problem_id'] +
                '/" method="post" enctype="multipart/form-data"><label for="file">File:</label><input type="file" name="file" id="file"><input type="submit" name="submit" value="Submit"></form>';
            var images = '<ul>';
            for (var j = 0; j < problem['images'].length; j++) {
                images += '<li><a href="' + problem['images'][j] +
                    '" target="_blank"><img src="' + problem[
                        'images'][j] +
                    '" style="max-width:100px" /></a></li>';
            }
            images += '</ul>';
            var authenticated = '';
            if (problem['is_authenticated'] == false) {
                authenticated = '[Not authenticated]';
            }
            $('#problems').append('<div id="problem_container_' +
                problem['problem_id'] + '"><div id="problem_' +
                problem['problem_id'] + '" class="' + problem[
                    'is_controlled'] + ' problem_label">' +
                problem['problem_name'] +
                ' <input type="button" value="Show problem" class="show_problem" id="control_display_for_problem_' +
                problem['problem_id'] +
                '" target="problem_data_' + problem[
                    'problem_id'] + '" problem="' + problem[
                    'problem_id'] + '" /> ' + authenticated +
                '</div><div class="problem_data" id="problem_data_' +
                problem['problem_id'] + '"><h4>Status</h4>' +
                status + '<h4>Notes</h4>' + notes +
                '<h4>Goals</h4>' + goals + '<h4>ToDo</h4>' +
                todos + '<h4>Images</h4>' + image_form + images +
                '<h4>Relationships</h4>' + relationships +
                '<h4>Guidelines</h4>' + guidelines +
                '</div></div>');
        }
        var html =
            '<input type="button" id="toggle_inactive_problems" value="Toggle inactive problems" /><div id="inactive_problems">';
        data = raw_data.problems['not_active'];
        window.problems = data.problems;
        //$('#problems').append(html);
        //html = '';
        for (var i = 0; i < data.length; i++) {
            var problem = data[i];
            relationships = '<ul>';
            var select = '<select class="problem_parent" parent="' +
                problem['problem_id'] + '">';
            select += '<option value="none">none</option>';
            for (var j = 0; j < data.length; j++) {
                if (data[j]['problem_name'] != problem[
                    'problem_name']) {
                    selected = '';
                    if (data[j]['problem_id'] == problem[
                        'effected_by']) {
                        selected = ' selected';
                    }
                    select += '<option value="' + problem[
                        'problem_id'] + '"' + selected + '>';
                    select += problem['problem_name'] + '</option>';
                }
            }
            select += '</select>';
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
            relationships += '<li><strong>Effected by:</strong> ' +
                select + '</li>';
            relationships += '<li><strong>Affects:</strong> ' +
                affects + '</li></ul>';
            if (problem['is_authenticated'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status =
                '<ul><li><input class="status" attr="authenticated" id="' +
                problem['problem_id'] + '" ';
            status += 'type="checkbox" ' + checked +
                '/> Is authenticated</li>';
            if (problem['is_controlled'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status +=
                '<li><label><input type="checkbox" attr="is_controlled" id="' +
                problem['problem_id'] + '" ' + checked +
                '/></label> ';
            status += 'Is controlled</li>';
            if (problem['is_active'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status +=
                '<li><label><input type="checkbox" attr="is_active" target="problem" id="' +
                problem['problem_id'] + '" ' + checked +
                '/><label> ';
            status += 'Is active</li>';
            status += '</ul>';
            guidelines = '<ul>';
            for (var j = 0; j < problem['guidelines'].length; j++) {
                guidelines += '<li>' + problem['guidelines'][j][
                    'guideline'
                ];
                guidelines += ' <a href="' + problem['guidelines'][
                    j
                ]['reference_url'] + '">';
                guidelines += problem['guidelines'][j][
                    'reference_url'
                ] + '</a></li>';
            }
            guidelines += '</ul>';
            // Goals: A problem may have zero to many associated with it.  Goals are a way for a patient to define and manage activities that they believe will be of value to them as an individual.  Goals are displayed with the red/green control state.  The goals that have not been set to 'accomplished' are displayed in the problem they are related to.  The note associated with a goal is to describe the motivation for adding that goal.  A GOAL DOES NOT HAVE TO BE ASSOCIATED WITH A PROBLEM.
            goals = '<ul id="goals_' + problem['problem_id'] +
                '" title="goal_' + problem['problem_id'] + '">';
            goals +=
                '<li><strong>Add:</strong> <input type="text" id="goal_input_' +
                problem['problem_id'] + '" />';
            goals += '<input type="button" value="Submit" parent="' +
                problem['problem_id'] + '" ';
            goals += 'target="goal_input_' + problem['problem_id'] +
                '" object_type="goal" class="submit_data" /></li>';
            for (var j = 0; j < problem['goals'].length; j++) {
                if (problem['goals'][j]['accomplished'] == true) {
                    checked = ' checked ';
                } else {
                    checked = '';
                }
                if (problem['goals'][j]['is_controlled'] == true) {
                    is_controlled_checked = ' checked ';
                } else {
                    is_controlled_checked = '';
                }
                notes = '<div id="goal_notes_' + problem['goals'][j]
                    ['id'] + '" class="goal_notes">';
                notes += '<strong>Start date:</strong> ' + problem[
                    'goals'][j]['start_date'];
                notes +=
                    '<br/><label><input type="checkbox" attr="goal" id="' +
                    problem['goals'][j]['id'] + '" ' + checked +
                    '/></label> ';
                notes +=
                    '<strong>Is accomplished</strong><br/><label><input type="checkbox" aswhat="controlled" label="' +
                    problem['goals'][j]['goal'] + ' (for probelm ' +
                    problem['problem_name'] +
                    ')" attr="goal_is_controlled" </label>';
                notes += 'id="' + problem['goals'][j]['id'] + '" ' +
                    is_controlled_checked + '/> ';
                notes +=
                    '<strong>Currently succeeding</strong><br/><table id="note_' +
                    problem['problem_id'] + '">';
                var role =
                    "{% if user_role == 'admin' %}physician{% else %}{{ user_role }}{% endif %}";
                current_physician_note = '';
                if (problem['goals'][j]['notes'].length > 0) {
                    current_physician_note = problem['goals'][j][
                        'notes'
                    ][0]['note'];
                    console.log(current_physician_note);
                    current_physician_note =
                        '<strong>Physician note:<br></strong><textarea id="note_input_for_goal_' +
                        problem['goals'][j]['id'] + '" value="' +
                        current_physician_note + '" cols="50" >' +
                        current_physician_note +
                        '</textarea><input type="button" value="Submit" parent="' +
                        problem['goals'][j]['id'] +
                        '" target="note_input_for_goal_' + problem[
                            'goals'][j]['id'] +
                        '" object_type="note_for_goal" class="submit_data" />';
                } else {
                    current_physician_note =
                        '<strong>Physician note:<br></strong><textarea id="note_input_for_goal_' +
                        problem['goals'][j]['id'] + '" value="' +
                        current_physician_note +
                        '" cols="50" /><input type="button" value="Submit" parent="' +
                        problem['goals'][j]['id'] +
                        '" target="note_input_for_goal_' + problem[
                            'goals'][j]['id'] +
                        '" object_type="note_for_goal" class="submit_data" />';
                }
                notes += current_physician_note;
                //notes += '</table></div>';
                goals += '<li id="goal_' + problem['goals'][j]['id'] +
                    '" class="' + problem['goals'][j][
                        'is_controlled'
                    ] + '">' + problem['goals'][j]['goal'] +
                    '<input type="button" class="show_goal" value="Show goal" target="goal_notes_' +
                    problem['goals'][j]['id'] + '" goal="' +
                    problem['goals'][j]['id'] + '" />' + notes +
                    '</li>';
            }
            goals += '</ul>';
            todos = '<ul id="todo_' + problem['problem_id'] + '">';
            todos +=
                '<li><strong>Add:</strong> <input type="text" id="todo_input_' +
                problem['problem_id'] +
                '" /><input type="button" value="Submit" parent="' +
                problem['problem_id'] + '" target="todo_input_' +
                problem['problem_id'] +
                '" object_type="todo" class="submit_data" /></li>';
            for (var j = 0; j < problem['todos'].length; j++) {
                if (problem['todos'][j]['accomplished'] == true) {
                    checked = ' checked ';
                } else {
                    checked = '';
                }
                todos +=
                    '<li><input type="checkbox" attr="todo" id="' +
                    problem['todos'][j]['id'] + '" ' + checked +
                    '/>' + problem['todos'][j]['todo'] + '</li>';
            }
            todos += '</ul>';
            // Notes: both the physian and the patient have their own note space for documenting the problem.  A physician can only edit the physician's note, and a physician can ONLY view the patient's note.  A patient can ONLY view the physician's note, and a patient can edit a patient note.  The most recent version of a note is read from database each time the problem is visited.
            notes = '<table id="note_' + problem['problem_id'] +
                '">';
            var role =
                "{% if user_role == 'admin' %}physician{% else %}{{ user_role }}{% endif %}";
            current_physician_note = '';
            if (problem['notes']['by_physician'].length > 0) {
                current_physician_note = problem['notes'][
                    'by_physician'
                ][0]['note'];
                if (role == 'physician') {
                    current_physician_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_physician_note + '">' +
                        current_physician_note +
                        '</textarea><input type="button" value="Submit" parent="' +
                        problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            } else {
                if (role == 'physician') {
                    current_physician_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_physician_note + '">' +
                        current_physician_note +
                        '</textarea><input type="button" value="Submit" parent="' +
                        problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            }
            current_patient_note = '';
            if (problem['notes']['by_patient'].length > 0) {
                current_patient_note = problem['notes'][
                    'by_patient'
                ][0]['note'];
                if (role == 'patient') {
                    current_patient_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_patient_note + '">' +
                        current_patient_note +
                        '</textarea><input type="button" value="Submit" parent="' +
                        problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            } else {
                if (role == 'patient') {
                    current_patient_note =
                        '<textarea id="note_input_' + problem[
                            'problem_id'] + '" value="' +
                        current_patient_note + '">' +
                        current_patient_note +
                        '</textarea><input type="button" value="Submit" parent="' +
                        problem['problem_id'] +
                        '" target="note_input_' + problem[
                            'problem_id'] +
                        '" object_type="note" class="submit_data" />';
                }
            }
            //notes += '<tr><td colspan="2"><strong>Add:</strong> <textarea id="note_input_'+problem['problem_id']+'" value="'+current_physician_note+'">'+current_physician_note+'</textarea><input type="button" value="Submit" parent="'+problem['problem_id']+'" target="note_input_'+problem['problem_id']+'" object_type="note" class="submit_data" /></td></tr>';
            notes +=
                '<tr><th>By physician</th><th>By patient</th></tr>';
            notes += '<tr><td>' + current_physician_note +
                '</td><td>' + current_patient_note + '</td></tr>';
            //for (var j=0;j<problem['notes'].length;j++) {
            //    notes += '<tr><td colspan="5">(by '+problem['notes'][j]['by']+') '+problem['notes'][j]['note']+'</td></tr>';
            //}
            notes += '</table>';
            var image_form =
                '<form action="/upload_image_to_problem/' + problem[
                    'problem_id'] +
                '/" method="post" enctype="multipart/form-data"><label for="file">File:</label><input type="file" name="file" id="file"><input type="submit" name="submit" value="Submit"></form>';
            var images = '<ul>';
            for (var j = 0; j < problem['images'].length; j++) {
                images += '<li><a href="' + problem['images'][j] +
                    '" target="_blank"><img src="' + problem[
                        'images'][j] +
                    '" style="max-width:100px" /></a></li>';
            }
            images += '</ul>';
            var authenticated = '';
            if (problem['is_authenticated'] == false) {
                authenticated = '[Not authenticated]';
            }
            //$('#problems').append('<div id="problem_container_'+problem['problem_id']+'"><div id="problem_'+problem['problem_id']+'" class="'+problem['is_controlled']+' problem_label">INACTIVE: '+problem['problem_name']+' <input type="button" value="Show problem" class="show_problem" id="control_display_for_problem_'+problem['problem_id']+'" target="problem_data_'+problem['problem_id']+'" problem="'+problem['problem_id']+'" /> '+authenticated+'</div><div class="problem_data" id="problem_data_'+problem['problem_id']+'"><h4>Notes</h4>'+notes+'<h4>Goals</h4>'+goals+'<h4>ToDo</h4>'+todos+'<h4>Images</h4>'+image_form+images+'<h4>Relationships</h4>'+relationships+'<h4>Status</h4>'+status+'<h4>Guidelines</h4>'+guidelines+'</div></div>');
            html += '<div id="problem_container_' + problem[
                    'problem_id'] + '"><div id="problem_' + problem[
                    'problem_id'] + '" class="' + problem[
                    'is_controlled'] + ' problem_label">INACTIVE: ' +
                problem['problem_name'] +
                ' <input type="button" value="Show problem" class="show_problem" id="control_display_for_problem_' +
                problem['problem_id'] + '" target="problem_data_' +
                problem['problem_id'] + '" problem="' + problem[
                    'problem_id'] + '" /> ' + authenticated +
                '</div><div class="problem_data" id="problem_data_' +
                problem['problem_id'] + '"><h4>Status</h4>' +
                status + '<h4>Notes</h4>' + notes +
                '<h4>Goals</h4>' + goals + '<h4>ToDo</h4>' + todos +
                '<h4>Images</h4>' + image_form + images +
                '<h4>Relationships</h4>' + relationships +
                '<h4>Guidelines</h4>' + guidelines + '</div></div>';
        }
        html += '</div>';
        $('#problems').append(html);
        $('#goals').html('');
        var goals = raw_data['goals']['not_accomplished'];
        for (var i = 0; i < goals.length; i++) {
            var goal = goals[i];
            status = '<ul>';
            status += '<li><strong>Start date:</strong> ' + goal[
                'start_date'] + '</li>';
            if (goal['is_controlled'] == true) {
                checked = ' checked ';
            } else {
                checked = '';
            }
            status +=
                '<li><labe><input type="checkbox" target="goal" aswhat="controlled"  attr="goal_is_controlled" id="' +
                goal['goal_id'] + '" ' + checked + '/> </labe>';
            status += 'Currently succeeding</li>';
            status +=
                '<li><label><input type="checkbox" target="goal" aswhat="accomplished" attr="goal" id="' +
                goal['goal_id'] + '" /> </label>';
            status += 'Is accomplished</li>';
            current_physician_note = '';
            if (goal['notes'].length > 0) {
                current_physician_note = goal['notes'][0]['note'];
                console.log(current_physician_note);
                current_physician_note =
                    '<strong>Motivation for setting this goal:</strong><br/><textarea id="note_input_for_goal_' +
                    goal['goal_id'] + '" value="' +
                    current_physician_note + '">' +
                    current_physician_note +
                    '</textarea><input type="button" label="' +
                    goal['goal'] + for_problem +
                    '" value="Submit" parent="' + goal['goal_id'] +
                    '" target="note_input_for_goal_' + goal[
                        'goal_id'] +
                    '" object_type="note_for_goal" class="submit_data" />';
            } else {
                current_physician_note =
                    '<strong>Motivation for setting this goal:</strong><br/><textarea id="note_input_for_goal_' +
                    goal['goal_id'] + '" value="' +
                    current_physician_note +
                    '" /><input type="button" value="Submit" label="' +
                    goal['goal'] + for_problem + '" parent="' +
                    goal['goal_id'] +
                    '" target="note_input_for_goal_' + goal[
                        'goal_id'] +
                    '" object_type="note_for_goal" class="submit_data" />';
            }
            status += '<li>' + current_physician_note + '</li>';
            status += '</ul>';
            if (goal['for_problem'] == '') {
                var for_problem = '';
            } else {
                var for_problem = ' (for problem ' + goal[
                    'for_problem'] + ')';
            }
            html = '<div id="goal_' + goal['goal_id'] + '" class="' +
                goal['is_controlled'] + '">' + goal['goal'] +
                for_problem;
            html += ' <input type="button" goallabel="' + goal[
                    'goal'] + for_problem + '" target="goal_data_' +
                goal['goal_id'] + '" goal="' + goal['goal_id'] +
                '" class="show_nonproblem_goal" value="Show goal" />';
            html += '</div>';
            html += '<div class="goal_data" id="goal_data_' + goal[
                'goal_id'] + '">' + status;
            html += '</div>';
            $('#goals').append(html)
        }
        $('#todos').html('');
        var todos = raw_data['todos']['not_accomplished'];
        for (var i = 0; i < todos.length; i++) {
            var todo = todos[i];
            status = '<ul>';
            status +=
                '<li><label><input type="checkbox" attr="todo" id="' +
                todo['todo_id'] + '" ' + checked + '/> </label>';
            status += 'Is accomplished</li>';
            status += '</ul>';
            if (todo['for_problem'] == '') {
                var for_problem = '';
            } else {
                var for_problem = ' (for problem ' + todo[
                    'for_problem'] + ')';
            }
            html =
                '<div><input type="checkbox" target="todo" attr="accomplished" ';
            html += 'id="' + todo['todo_id'] + '" content="' + todo[
                    'todo'] + for_problem + '" /> ' + todo['todo'] +
                for_problem;
            html +=
                ' <!--<input class="mark_working_on" type="button" value="I\'m working on this todo" ';
            html += 'summary="Working on todo &quot;' + todo['todo'] +
                for_problem + '&quot;" />-->';
            html += '</div>';
            $('#todos').append(html)
        }
        $('#accomplished_todos').html('');
        var todos = raw_data['todos']['accomplished'];
        for (var i = 0; i < todos.length; i++) {
            var todo = todos[i];
            if (todo['for_problem'] == '') {
                var for_problem = '';
            } else {
                var for_problem = ' (for problem ' + todo[
                    'for_problem'] + ')';
            }
            html =
                '<div><input type="checkbox" checked target="todo" attr="accomplished" id="' +
                todo['todo_id'] + '" /> ' + todo['todo'] +
                for_problem;
            html += '</div>';
            $('#accomplished_todos').append(html)
        }
        if (typeof window.current_problem != 'undefined') {
            $('#show').html($('#problem_container_' + window.current_problem)
                .html());
            $('#show > #problem_' + window.current_problem).css({
                'display': 'block',
                'position': 'fixed',
                'z-index': 2,
                'top': '0',
                'left': '0',
                'width': '100%'
            });
            var bottom = $('#show > #problem_' + window.current_problem)
                .position().top + $('#problem_' + window.current_problem)
                .outerHeight(true);
            $('#' + $(this).attr('target')).css({
                'display': 'block',
                'position': 'absolute',
                'z-index': 1,
                'top': bottom,
                'right': 0,
                'left': '0',
                'min-height': '100%'
            })
            $('#show > #problem_' + window.current_problem).css({
                'display': 'block',
                'position': 'fixed',
                'z-index': 2,
                'top': '0',
                'left': '0',
                'width': '100%'
            });
            var bottom = $('#show > #problem_' + window.current_problem)
                .position().top + $('#problem_' + window.current_problem)
                .outerHeight(true);
            $('#problem_data_' + window.current_problem).css({
                'display': 'block',
                'position': 'absolute',
                'z-index': 1,
                'top': bottom,
                'right': 0,
                'left': '0',
                'min-height': '100%'
            })
            $('#control_display_for_problem_' + window.current_problem)
                .val('Hide problem');
            $('#control_display_for_problem_' + window.current_problem)
                .removeClass();
            $('#control_display_for_problem_' + window.current_problem)
                .addClass('hide_problem');
        }
    }); 
}
