function generateProblemTodosHtml(problemJson) {
    var problemTodosHtml = '';
    todos = '<ul id="todo_' + problemJson['problem_id'] + '">';
    todos +=
        '<li><strong>Add:</strong> <input type="text" id="todo_input_' +
        problemJson['problem_id'] +
        '" /><input type="button" value="Submit" parent="' +
        problemJson['problem_id'] + '" target="todo_input_' +
        problemJson['problem_id'] +
        '" object_type="todo" class="submit_data" /></li>';
    for (var j = 0; j < problem['todos'].length; j++) {
        if (problemJson['todos'][j]['accomplished'] == true) {
            checked = ' checked ';
        } else {
            checked = '';
        }
        todos +=
            '<li><input type="checkbox" attr="todo" id="' +
            problemJson['todos'][j]['id'] + '" ' + checked +
            '/>' + problemJson['todos'][j]['todo'] + '</li>';
    }
    todos += '</ul>';
    return problemTodosHtml;
}
