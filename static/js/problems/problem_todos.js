function generateProblemTodosHtml(problemJson) {
    var problemTodosHtml = '';
    problemTodosHtml = '<ul id="todo_' + problemJson['problem_id'] + '">';
    problemTodosHtml +=
        '<li><strong>Add:</strong> <input type="text" id="todo_input_' +
        problemJson['problem_id'] +
        '" /><input type="button" value="Submit" parent="' +
        problemJson['problem_id'] + '" target="todo_input_' +
        problemJson['problem_id'] +
        '" object_type="todo" class="submit_data" /></li>';
    for (var j = 0; j < problemJson['todos'].length; j++) {
        if (problemJson['todos'][j]['accomplished'] == true) {
            checked = ' checked ';
        } else {
            checked = '';
        }
        problemTodosHtml +=
            '<li><input type="checkbox" attr="todo" id="' +
            problemJson['todos'][j]['id'] + '" ' + checked +
            '/>' + problemJson['todos'][j]['todo'] + '</li>';
    }
    problemTodosHtml += '</ul>';
    return problemTodosHtml;
}
