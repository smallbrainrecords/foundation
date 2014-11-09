function getProblemHtml(problemJson) {
    var problemElements = ['Status', 'Notes', 'Goals', 'Todos', 'Images', 'Relationships', 'Guidelines', 'History'];
    var problemHtml = '';
    problemElements.forEach(function(problemElement) {
        problemHtml += '<h4>'+problemElement+'</h4>';
        problemHtml += '<div>';
        problemHtml += window["generate"+problemElement+"Html"](problemJson);
        problemHtml += '</div>';
    });
    
    return problemHtml;
}
