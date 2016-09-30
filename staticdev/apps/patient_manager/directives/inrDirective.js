var inr = angular.module('inr', []);

inr.directive('inr', ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', 'inrService', inrDirective]);

function inrDirective(CollapseService, toaster, $location, $timeout, prompt, inrService) {

    var inrObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/inr.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('inr.patient', function(newVal, oldVal) {
                        if(newVal) {
                            scope.inr = scope.$eval(attr.ngModel);
                            
                            scope.open_inr = function(){
                                if (!scope.show_inr_collapse) {
                                    CollapseService.ChangeInrCollapse();
                                    scope.show_inr_collapse = CollapseService.show_inr_collapse;
                                }
                                else {
                                    CollapseService.ChangeInrCollapse();
                                    scope.show_inr_collapse = CollapseService.show_inr_collapse;
                                }
                            };

                            scope.add_medication = function(form) {
                                if (form.name == '') return;
                                form.inr_id = scope.inr.id;
                                form.patient_id = scope.patient_id;
                                inrService.addMedication(form).then(function(data) {
                                    scope.inr.inr_medications.push(data['medication']);
                                    form.name = '';
                                    toaster.pop('success', 'Done', 'Added medication!');
                                });
                            };

                            scope.dosage_increase = function(medication) {
                                if (medication.concept_id == null) {
                                    prompt({
                                        "message": "This is largest dosage form"
                                    }).then(function(result){
                                        return false;
                                    },function(){
                                        return false;
                                    });
                                }
                            };

                            scope.dosage_decrease = function(medication) {
                                if (medication.concept_id == null) {
                                    prompt({
                                        "message": "This is smallest dosage form"
                                    }).then(function(result){
                                        return false;
                                    },function(){
                                        return false;
                                    });
                                }
                            };

                            scope.see_medication_history = function(medication) {
                                medication.show_medication_history = !medication.show_medication_history;
                            };

                            scope.add_note = function(form, medication) {
                                if (form.note == '') return;
                                form.medication_id = medication.id;
                                form.patient_id = scope.patient_id;
                                inrService.addMedicationNote(form).then(function(data) {
                                    medication.medication_notes.push(data['note']);
                                    toaster.pop('success', 'Done', 'Added note!');
                                });
                            };

                            scope.edit_note = function(note) {
                                note.show_edit_note = !note.show_edit_note;
                            };

                            scope.save_note = function(note) {
                                inrService.editNote(note).then(function(data) {
                                    note.show_edit_note = false;
                                    toaster.pop('success', 'Done', 'Edited note successfully');
                                });
                            };

                            scope.delete_note = function(note, medication) {
                                prompt({
                                    "title": "Are you sure?",
                                    "message": "Deleting a note is forever. There is no undo."
                                }).then(function(result){
                                    inrService.deleteNote(note).then(function(data){
                                        var index = medication.medication_notes.indexOf(note);
                                        medication.medication_notes.splice(index, 1);
                                        toaster.pop('success', 'Done', 'Deleted note successfully');
                                    });
                                },function(){
                                    return false;
                                });
                            }
                        }
                    }, true);
                }
            }

};
