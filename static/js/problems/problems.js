function generateProblemHtml(problemJson) {
    var authenticated = '';
    if (problemJson['is_authenticated'] == false) {
        authenticated = '[Not authenticated]';
    }
    
    var problemHtml = '<div id="problem_container_' +
        problemJson['problem_id'] + '"><div id="problem_' +
        problemJson['problem_id'] + '" class="' + problemJson[
            'is_controlled'] + ' problem_label">' +
        problemJson['problem_name'] +
        ' <input type="button" value="Show problem" class="show_problem" id="control_display_for_problem_' +
        problemJson['problem_id'] +
        '" target="problem_data_' + problemJson[
            'problem_id'] + '" problem="' + problemJson[
            'problem_id'] + '" /> ' + authenticated +
        '</div><div class="problem_data" id="problem_data_' +
        problemJson['problem_id'] + '">';
    var problemElements = ['Status', 'Notes', 'Goals', 'Todos', 'Images', 'Relationships', 'Guidelines', 'History'];    
    problemElements.forEach(function(problemElement) {
        problemHtml += '<h4>'+problemElement+'</h4>';
        problemHtml += '<div>';
        problemHtml += window["generateProblem"+problemElement+"Html"](problemJson);
        problemHtml += '</div>';
    });
    problemHtml += '</div>';
    
    return problemHtml;
}

function generateProblemsHtmlForActiveStatus(patientJson, activeStatus) {
    var problemsJsonForActiveStatus = patientJson[activeStatus];
    var problemsJsonForActiveStatusHtml = '';
    for (var i=0;i<problemsJsonForActiveStatus.length;i++) {
        var problemJson = problemsJsonForActiveStatus[i];
        problemsJsonForActiveStatusHtml += getProblemHtml(problemJson);
    }
    return problemsJsonForActiveStatusHtml;
}

function generateProblemsHtml(patientJson) {
    var problemsHtml = '';
    problemsHtml += generateProblemsHtmlForActiveStatus(patientJson, 'is_active');
    problemsHtml += '<input type="button" id="toggle_inactive_problems" value="Toggle inactive problems" />'
        + '<div id="inactive_problems">';
    problemsHtml += generateProblemsHtmlForActiveStatus(patientJson, 'not_active');
    problemsHtml += '</div>';
}
