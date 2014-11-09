function generateProblemNotesForRoleHtml(problemJson, role) {
    problemNotesForRoleHtml = '<div><h5>'+role.capitalize()+' note</h5>';
    if (problem['notes']['by_'+role].length > 0) {
        current_physician_note = problem['notes'][
            'by_' + role
        ][0]['note'];
        if (userRole == role) {
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
        if (userRole == role) {
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
        } else {
            problemNotesForRoleHtml += '<p>None</p>'
        }
    }
    problemNotesForRoleHtml += '</div>';
}

function generateProblemNotesHtml(problemJson) {
    var problemNotesHtml = '';
    problemNotesHtml += generateProblemNotesForRoleHtml(problemJson, 'physician');
    problemNotesHtml += generateProblemNotesForRoleHtml(problemJson, 'patient');
    return problemNotesHtml;
}
