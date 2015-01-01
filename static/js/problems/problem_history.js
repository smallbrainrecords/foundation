function generateProblemHistoryHtml(problemJson) {
    var problemHistoryHtml = '';
    problemHistoryHtml = '<p><strong>Start date:</strong> ';
    problemHistoryHtml += '<input type="text" id="problem_start_date_' + problemJson['problem_id'] + '" </p>';
    return problemHistoryHtml;
}
