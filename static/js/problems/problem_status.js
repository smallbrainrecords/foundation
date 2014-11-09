String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

function generateProblemStatusHtml(problemJson) {
    var problemStatusHtml = '';
    var problemStatusItems = ["is_controlled", "is_authenticated", "is_active"];
    problemStatusElements.forEach(function(problemStatusElement) {
        if (problemJson[problemStatusElement] == true) {
            var checked = ' checked ';
        } else {
            var checked = '';
        }
        var problemStatusElementDisplayName = problemStatusElement.replace("_", " ").capitalize();
        problemStatusHtml += '<input type="checkbox" attr="'+problemStatusElement+'" target="problem" id="' +
        problemJson['problem_id'] + '" ' + checked + '/> '+problemStatusElementDisplayName;
    });
    return problemStatusHtml;
}
