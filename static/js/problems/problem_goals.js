/*
* this displays goals that are associated with problems
*
* goal start date is the date goal was created.
* goals may be associated with a particular problem or independent of a problem.
* goal is_controlled means that the goal is being met and is still active, it will have a green color if controlled, red if not.
* goal is_accomplished determines if the goal is still visible or active.
*/

function generateProblemGoalStartDateHtml(goal) {
    return '<strong>Start date:</strong> ' + goal['start_date'];
}

function generateProblemGoalIsAccomplishedHtml(goal) {
    if (goal['is_controlled'] == true) {
        is_controlled_checked = ' checked ';
    } else {
        is_controlled_checked = '';
    }
    return '<strong>Is accomplished</strong><br/><label><input type="checkbox" aswhat="controlled" label="' +
            goal['goal'] + ' (for problem ' +
            problem['problem_name'] +
            ')" attr="goal_is_controlled" id="' + goal['goal'] + '" ' +
            is_controlled_checked + '/> ';
}

function generateProblemGoalCurrentlySuceedingHtml(goal) {
    return '<strong>Currently succeeding</strong>';
}
function generateProblemGoalHtml(goal) {
    problemGoalHtml = '<li id="goal_' + goal['id'] +
            '" class="' + goal[
                'is_controlled'
            ] + '">' + goal['goal'] +
            '<input type="button" class="show_goal" value="Show goal" target="goal_notes_' +
            goal['id'] + '" goal="' +
            goal['id'] + '" /></li>';
    var problemGoalElements = ['StartDate', 'IsAccomplished', 'CurrentlySuceeding'];    
    problemGoalElements.forEach(function(problemGoalElement) {
        problemGoalHtml += window["generateProblemGoal"+problemGoalElement+"Html"](goal);
    });
    return problemGoalHtml;
}

function generateProblemGoalsHtml(problem) {
    var problemGoalsHtml = '<ul id="goals_' + problem['problem_id'] +
        '" title="goal_' + problem['problem_id'] + '">';
    problemGoalsHtml +=
        '<li><strong>Add:</strong> <input type="text" id="goal_input_' +
        problem['problem_id'] + '" />';
    problemGoalsHtml += '<input type="button" value="Submit" parent="' +
        problem['problem_id'] + '" ';
    problemGoalsHtml += 'target="goal_input_' + problem['problem_id'] +
        '" object_type="goal" class="submit_data" /></li>';
    console.log(JSON.stringify(problem));
    if(Object.prototype.hasOwnProperty.call(problem, 'goals')) {
    for (var j = 0; j < problem['goals'].length; j++) {
        problemGoalsHtml += generateProblemGoalsHtml(problem['goals'][j]);
    }
    problemGoalsHtml += '</ul>';    
    return problemGoalsHtml;
}
