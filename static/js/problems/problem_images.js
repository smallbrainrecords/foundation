function generateProblemImagesHtml(problemJson) {
    var problemImagesHtml = '<form action="/upload_image_to_problem/' + problemJson[
            'problem_id'] +
        '/" method="post" enctype="multipart/form-data"><label for="file">File:</label>' +
        '<input type="file" name="file" id="file"><input type="submit" name="submit" value="Submit"></form>';
    var problemImagesHtml = '<ul>';
    for (var j = 0; j < problemJson['images'].length; j++) {
        problemImagesHtml += '<li><a href="' + problemJson['images'][j] +
            '" target="_blank"><img src="' + problemJson[
                'images'][j] +
            '" style="max-width:100px" /></a></li>';
    }
    problemImagesHtml += '</ul>';
    return problemImagesHtml;
}
