$(function() {
    $(document).on("change", "input:checkbox", function(e) {
        var saved_encounter = false;
        //alert($(this).is(':checked')+$(this).attr('id'));
        if ($(this).attr('attr') == 'is_controlled') {
            $("#problem_" + $(this).attr('id')).removeClass();
            $("#problem_" + $(this).attr('id')).addClass($(this).is(':checked').toString());
            if ($(this).is(':checked') == true) {
                var marked_as = 'controlled';
            } else {
                var marked_as = 'not controlled';
            }
            $.post('/save_encounter_event/', {
                'summary': 'Marked problem "' + $('#problem_' + $(this).attr('id')).text() + '" as ' + marked_as,
                'encounter_id': window.encounter_id,
                'patient_id': patient.id});
            var target = 'problem';
            saved_encounter = true;
        } else if ($(this).attr('attr') == 'goal' || $(this).attr('attr') == 'todo' || $(this).attr('attr') == 'goal_is_controlled') {
            var target = $(this).attr('attr');
            $("#goal_" + $(this).attr('id')).removeClass();
            $("#goal_" + $(this).attr('id')).addClass($(this).is(':checked').toString());

        } else if ($(this).attr('attr') != 'problem') {
            $.post('/change_status/', {
                'target': $(this).attr('target'),
                'id': $(this).attr('id'),
                'value': $(this).is(':checked'),
                'attr': $(this).attr('attr')
            });
            if ($(this).attr('attr') == 'accomplished' && $(this).attr('target') == 'todo') {
                $(this).parent().hide();
                var summary = 'Marked todo "' + $(this).attr('content') + '" as accomplised';
                $.post('/save_encounter_event/', {
                    'summary': summary,
                    'encounter_id': window.encounter_id,
                    'patient_id': patient.id});

            } else {
                if ($(this).attr('attr') == 'authenticated' && $(this).attr('target') == 'problem') {
                    if ($(this).is(':checked') == true) {
                        var marked_as = 'authenticated';
                    } else {
                        var marked_as = 'not authenticated';
                    }
                    var summary = 'Marked ' + $(this).attr('target') + ' "' + $('#problem_' + $(this).attr('id')).text() + '" as ' + marked_as;
                    $.post('/save_encounter_event/', {
                        'summary': summary,
                        'encounter_id': window.encounter_id,
                        'patient_id': patient.id});

                } else if ($(this).attr('attr') == 'is_active' && $(this).attr('target') == 'problem') {
                    if ($(this).is(':checked') == true) {
                        var marked_as = 'active';
                    } else {
                        var marked_as = 'not active';
                    }
                    var summary = 'Marked ' + $(this).attr('target') + ' "' + $('#problem_' + $(this).attr('id')).text() + '" as ' + marked_as;
                    $.post('/save_encounter_event/', {
                        'summary': summary,
                        'encounter_id': window.encounter_id,
                        'patient_id': patient.id});

                } else {
                    if ($(this).is(':checked') == true) {
                        var marked_as = $(this).attr('attr');
                    } else {
                        var marked_as = 'not ' + $(this).attr('attr');
                    }
                    var summary = 'Marked ' + $(this).attr('target') + ' "' + $(this).attr('label') + '" as ' + marked_as;
                    $.post('/save_encounter_event/', {
                        'summary': summary,
                        'encounter_id': window.encounter_id,
                        'patient_id': patient.id});
                }
            }
            saved_encounter = true;
        } else {
            var target = 'problem';
        }
        if (saved_encounter != true) {
            if ($(this).attr('attr') == 'accomplished' && $(this).attr('target') == 'todo') {
                $(this).parent().hide();
                var summary = 'Marked todo "' + $(this).attr('content') + '" as accomplised';
                $.post('/save_encounter_event/', {
                    'summary': summary,
                    'encounter_id': window.encounter_id,
                    'patient_id': patient.id});

            } else {
                if ($(this).is(':checked') == true) {
                    var marked_as = $(this).attr('aswhat');
                } else {
                    var marked_as = 'not ' + $(this).attr('aswhat');
                }
                var summary = 'Marked ' + $(this).attr('target') + ' "' + $(this).attr('label') + '" as ' + marked_as;
                $.post('/save_encounter_event/', {
                    'summary': summary,
                    'encounter_id': window.encounter_id,
                    'patient_id': patient.id});

            }
        }
        if ($(this).attr('attr') == 'accomplished' && $(this).attr('target') == 'todo') {
            $(this).parent().hide();
        }
        console.log('target: ' + target);
        $.post('/change_status/', {
            'target': target,
            'id': $(this).attr('id'),
            'value': $(this).is(':checked'),
            'attr': $(this).attr('attr')
        });

    });

    function makeid() {
        var text = "";
        var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

        for (var i = 0; i < 20; i++)
            text += possible.charAt(Math.floor(Math.random() * possible.length));

        return text;
    }
    var tracking_id = makeid();
    var old_status = '{}';

    function getStatus() {
        console.log('get stauts')
        $.get('/get_problems/'+patient.id, {
            'get_only_status': true,
            'tracking_id': tracking_id
        }, function(data) {
            $('#viewers').text(JSON.stringify(data.viewers));
            $('#viewers').append(JSON.stringify(data.view_status));
            if (old_status != JSON.stringify(data.view_status)) {
                var status = data.view_status;
                if (status.action == 'show') {
                    console.log('status: ' + status);
                    console.log('show: ' + status['show_what']);
                    $('#' + status.show_what[0]).show();
                    console.log('#control_display_for_' + status.scroll_to);

                    $(document).scrollTop($('#' + status.scroll_to).offset().top);
                    $('#control_display_for_' + status.scroll_to).attr('value', 'Hide problem');
                    $('#control_display_for_' + status.scroll_to).removeClass();
                    $('#control_display_for_' + status.scroll_to).addClass('hide_problem');
                    old_status = JSON.stringify(data.view_status);
                } else if (status.action == 'hide') {
                    updateProblems();
                    setTimeout(function() {
                        window.current_problem = null;
                        $('.problem_data').hide();
                    }, 2000);
                }
            }
            setTimeout(function() {
                getStatus();
            }, 800);
        });
    }
    $(document).on('change', '.problem_parent', function() {

        console.log('submitting new parent');
        var parent_id = $(this).attr('parent');

        var type = 'mark_parent';
        var val = $(this).val();

        $.post('/submit_data_for_problem/' + parent_id + '/', {
            'type': type,
            'data': val
        }, function() {
            console.log('parent changed')
        });

    });
    $(document).on('click', '#toggle_inactive_problems', function() {
        $('#inactive_problems').toggle()
    })
    $(document).on('click', '#toggle_accomplished_todos', function() {
        $('#accomplished_todos').toggle()
    })
    $(document).on('click', '.submit_data', function() {
        var parent_id = $(this).attr('parent');

        var type = $(this).attr('object_type');
        var val = $('#' + $(this).attr('target')).val();
        if (val != '') { // send to server }
            console.log(JSON.stringify({
                'parent': $(this).attr('parent'),
                'type': $(this).attr('object_type'),
                'data': val
            }));
            $.post('/submit_data_for_problem/' + $(this).attr('parent') + '/', {
                'type': $(this).attr('object_type'),
                'data': val
            }, function(data) {
                $('#' + type + '_' + parent_id).append('<li>' + val + '</li>');
                window.goal = data;
                console.log(data);
                updateProblems();
            });
        }
        if ($(this).attr('object_type') == 'note_for_goal') {
            $.post('/save_encounter_event/', {
                'summary': 'Changed moviation for goal ' + $(this).attr('label') + ' to: ' + val,
                'encounter_id': window.encounter_id,
                'patient_id': patient.id});

        } else {
            $.post('/save_encounter_event/', {
                'summary': 'Added ' + $(this).attr('object_type') + ' to ' + $(this).attr('parentlabel') + ': ' + val,
                'encounter_id': window.encounter_id,
                'patient_id': patient.id});
        }
        updateProblems();
        $(document).scrollTop($('#problem_' + window.current_problem).offset().top);
        setTimeout(function() {
            $('#problem_data_' + window.current_problem).show();
        }, 2000);
        //console.log($('#problem_data_'+window.current_problem).html());
        setTimeout(function() {
            $('#goal_notes_' + window.goal).show()
        }, 2000);
    }); 
    $('div').on('focusin', 'input:text', function() {
        if ($(this).attr('default') == $(this).val()) {
            $(this).val('');
        }
    });
    $('#addProblem').click(function() {
        if ($('#concept_id').val() == $('#concept_id').attr('default')) {
            concept_id = '';
        } else {
            concept_id = $('#concept_id').val();
        }
        if (jQuery.inArray(concept_id, Object.keys(window.concept_ids)) != -1 && (concept_id != '')) {
            var r = confirm("Go to existing problem");
            if (r == true) {
                window.current_problem = $(this).attr('problem');
                $('.problem_data').hide();
                var problem = window.concept_ids[concept_id];
                $('#problem_' + problem).show();
                $(document).scrollTop($('#problem_' + problem).offset().top);
            } else {
                $.post('/patient/'+patient.id+'/add_problem/', {
                    'problem_name': $('#problem_name').val(),
                    'concept_id': concept_id
                }, function(data) {
                    updateProblems();
                    $('#problem_name').val($('#problem_name').attr('default'));
                    $('#concept_id').val($('#concept_id').attr('default'));
                    $('#results').html('');
                });
                $.post('/save_encounter_event/', {
                    'summary': 'Added problem "' + $('#problem_name').val() + '"',
                    'encounter_id': window.encounter_id,
                    'patient_id': patient.id});

            }

            //$(this).val('Hide problem');
            //$(this).removeClass();
            //$(this).addClass('hide_problem');

            // THIS IS THE ENCOUNTER REFERENCE: 
            //$.post('/save_encounter_event/', {'summary': 'Physician clicked on problem: "'+$('#problem_'+$(this).attr('problem')).text()+'"', 'encounter_id': window.encounter_id, 'patient_id': {{ patient.id }}});

        } else {
            $.post('/patient/'+patient.id+'/add_problem/', {
                'problem_name': $('#problem_name').val(),
                'concept_id': concept_id
            }, function(data) {
                updateProblems();
                $('#problem_name').val($('#problem_name').attr('default'));
                $('#concept_id').val($('#concept_id').attr('default'));
                $('#results').html('');
            });
            $.post('/save_encounter_event/', {
                'summary': 'Added problem "' + $('#problem_name').val() + '"',
                'encounter_id': window.encounter_id,
                'patient_id': patient.id});
        }
    });
    $('#addGoal').click(function() {
        $.post('/patient/{{ patient.id }}/add_problem/', {
            'goal': $('#goal_description').val()
        }, function(data) {
            updateProblems();
            $('#goal_description').val($('goal_description').attr('default'));
        });
        $.post('/save_encounter_event/', {
            'summary': 'Added goal "' + $('#goal_description').val() + '"',
            'encounter_id': window.encounter_id,
            'patient_id': patient.id});

    });
    $('#addTodo').click(function() {
        console.log('add: todo' + $('#todo_description').val())
        $.post('/patient/{{ patient.id }}/add_problem/', {
            'todo': $('#todo_description').val()
        }, function(data) {
            updateProblems();
            $('#todo_description').val($('todo_description').attr('default'));
        });
        $.post('/save_encounter_event/', {
            'summary': 'Added todo "' + $('#todo_description').val() + '"',
            'encounter_id': window.encounter_id,
            'patient_id': patient.id});

    });
    $('body').on('click', '.show_problem', function() {
        window.current_problem = $(this).attr('problem');
        //$('#show').html('');
        $(this).val('Hide problem');
        $(this).removeClass();
        $(this).addClass('hide_problem');
        $('#hide').hide();
        $('.problem_data').hide();
        $('.problem_label').css({
            'position': 'inherit',
            'width': 'inherit'
        });
        console.log($('#problem_container_' + $(this).attr('problem')).html());
        $('#show').html($('#problem_container_' + $(this).attr('problem')).html());
        $('#show > #' + $(this).attr('target')).show();
        $('#show > #problem_' + $(this).attr('problem')).show()
        $('#show > #problem_' + $(this).attr('problem')).css({
            'display': 'block',
            'position': 'fixed',
            'z-index': 2,
            'top': '0',
            'left': '0',
            'width': '100%'
        });
        var bottom = $('#show > #problem_' + $(this).attr('problem')).position().top + $('#problem_' + $(this).attr('problem')).outerHeight(true);
        $('#' + $(this).attr('target')).css({
                'display': 'block',
                'position': 'absolute',
                'z-index': 1,
                'top': bottom,
                'right': 0,
                'left': '0',
                'min-height': '100%'
            })
            //$(document).scrollTop( $('#problem_'+$(this).attr('problem')).offset().top );  
        window.scrollTo(0, 0);
        $.get('/get_problems/{{ patient.id }}/', {
            'new_status': '{"scroll_to": "problem_' + $(this).attr('problem') + '", "action": "show", "show_what": ["' + $(this).attr('target') + '"]}'
        });
        // THIS IS THE ENCOUNTER REFERENCE: 
        $.post('/save_encounter_event/', {
            'summary': 'Clicked on problem: "' + $('#problem_' + $(this).attr('problem')).text() + '"',
            'encounter_id': window.encounter_id,
            'patient_id': patient.id });
    });
    $('body').on('click', '.show_nonproblem_goal', function() {
        $('.goal_data').hide();
        $('#' + $(this).attr('target')).show();
        $(document).scrollTop($('#goal_' + $(this).attr('goal')).offset().top);
        $(this).val('Hide goal');
        $(this).removeClass();
        $(this).addClass('hide_nonproblem_goal');
        //$.get('/get_problems/{{ patient.id }}/', {'new_status': '{"scroll_to": "problem_'+$(this).attr('problem')+'", "action": "show", "show_what": ["'+$(this).attr('target')+'"]}'});
        // THIS IS THE ENCOUNTER REFERENCE: 
        //$.post('/save_encounter_event/', {'summary': 'Physician clicked on goal: "'+$('#goal'+$(this).attr('goal')).text()+'"', 'encounter_id': window.encounter_id, 'patient_id': {{ patient.id }}});
        $.post('/save_encounter_event/', {
            'summary': 'Clicked on goal: "' + $(this).attr('goallabel') + '"',
            'encounter_id': window.encounter_id,
            'patient_id': patient.id});

    });
    $('body').on('click', '.hide_nonproblem_goal', function() {
        $('.goal_data').hide();
        $(document).scrollTop($('#goal_' + $(this).attr('goal')).offset().top);
        $(this).val('Show goal');
        $(this).removeClass();
        $(this).addClass('show_nonproblem_goal');
        //$.get('/get_problems/{{ patient.id }}/', {'new_status': '{"scroll_to": "problem_'+$(this).attr('problem')+'", "action": "show", "show_what": ["'+$(this).attr('target')+'"]}'});
        // THIS IS THE ENCOUNTER REFERENCE: 
        //$.post('/save_encounter_event/', {'summary': 'Physician clicked on problem: "'+$('#problem_'+$(this).attr('problem')).text()+'"', 'encounter_id': window.encounter_id, 'patient_id': {{ patient.id }}});
    });
    $('body').on('click', '.show_goal', function() {
        //window.current_problem = $(this).attr('problem');
        $('.goal_notes').hide();
        $('#' + $(this).attr('target')).show();
        //$(document).scrollTop( $('#goal_'+$(this).attr('goal')).offset().top );  
        $(this).val('Hide goal');
        $(this).removeClass();
        $(this).addClass('hide_goal');

        // THIS IS THE ENCOUNTER REFERENCE: 
        // $('#problem_'+$(this).attr('problem')).text()
        console.log('show goal');
        console.log('goal label:' + $(this).attr('goallabel'));
        //$.post('/save_encounter_event/', {'summary': 'Clicked on goal: "'+$(this).attr('goallabel')+'"', 'encounter_id': window.encounter_id, 'patient_id': {{ patient.id }}});
    });
    $('body').on('click', '.hide_problem', function() {
        $('#show').html('');
        $('#hide').show();
        $('.problem_label').css({
            'position': 'inherit',
            'width': 'inherit'
        });
        window.current_problem = null;
        $('.problem_data').hide();
        $('.hide_problem').val('Show problem');
        $('.hide_problem').removeClass().addClass('show_problem');
        $.get('/get_problems/'+patient.id, {
            'new_status': '{"action": "hide"}'
        });
        $(document).scrollTop($('#problem_' + $(this).attr('problem')).offset().top);
    });
    $('body').on('click', '.hide_goal', function() {
        //window.current_problem = null;
        $('.goal_notes').hide();
        $(this).val('Show goal');
        $(this).removeClass();
        $(this).addClass('show_goal');
    });
    var timeout;
    $('#problem_name').keyup(function() {
        var target = $(this);
        window.clearTimeout(timeout);
        timeout = window.setTimeout(function() {
            $('#results').html('Searching for ' + target.val());
            $.get('/list_terms/', {
                'query': target.val()
            }, function(data) {
                $('#results').html('<ul>');
                $('#results').append('<li>Results for ' + target.val() + '</li>');
                for (var i = 0; i < data.length; i++) {
                    $('#results').append('<li><input class="select_concept" type="button" concept_id="' + data[i]["code"] + '" value="' + data[i]["term"] + '" /></li>');
                }
                $('#results').append('</ul>');
            });

        }, 500);
    });
    $('body').on('click', '.select_concept', function() {
        $('#problem_name').val($(this).val());
        $('#concept_id').val($(this).attr('concept_id'));
        $(document).scrollTop($('#add_problem_div').offset().top);
    });
});
