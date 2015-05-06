function generateProblemGuidelinesHtml(problemJson) {
    var problemGuidelinesHtml = '';
    problemGuidelinesHtml = '<ul>';
    for (var j = 0; j < problemJson['guidelines'].length; j++) {
        problemGuidelinesHtml += '<li>' + problemJson['guidelines'][j][
            'guideline'
        ];
        problemGuidelinesHtml += ' <a href="' + problemJson['guidelines'][
            j
        ]['reference_url'] + '">';
        problemGuidelinesHtml += problemJson['guidelines'][j][
            'reference_url'
        ] + '</a></li>';
    }
    problemGuidelinesHtml += '</ul>';
    return problemGuidelinesHtml;
}
