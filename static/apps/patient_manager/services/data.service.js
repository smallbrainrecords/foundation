(function () {

    'use strict';

    angular.module('ManagerApp').service('dataService',
        function ($http, $q, $cookies, httpService) {

            return {
                csrf_token: csrf_token,
                fetchDataInfo: fetchDataInfo,
                fetchPinToProblem: fetchPinToProblem,
                dataPinToProblem: dataPinToProblem,
                addData: addData,
                fetchIndividualDataInfo: fetchIndividualDataInfo,
                deleteIndividualData: deleteIndividualData,
                saveData: saveData,
                saveDataType: saveDataType,
                deleteData: deleteData,
                updateGraphType: updateGraphType,
                generateChartData: generateChartData,
                generateChartLabel: generateChartLabel,
                generateChartSeries: generateChartSeries,
                generateMostRecentValue: generateMostRecentValue,
                updateViewMode: updateViewMode,
                getValueCount: getValueCount,
                generateMostCommonData: generateMostCommonData,
                deleteComponentValues: deleteComponentValues
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function fetchDataInfo(data_id) {
                var url = `/data/${data_id}/info`;
                var params = {};

                return httpService.get(params, url);

            }

            function fetchPinToProblem(data_id) {
                var url = `/data/${data_id}/get_pins`;
                var params = {};

                return httpService.get(params, url);

            }

            function dataPinToProblem(patient_id, form) {
                var url = `/data/${patient_id}/pin_to_problem`;
                return httpService.post(form, url);
            }

            function addData(patient_id, component_id, form) {
                var url = `/data/${patient_id}/${component_id}/add_new_data`;
                return httpService.post(form, url);
            }

            function fetchIndividualDataInfo(patient_id, component_id) {
                var url = `/data/${patient_id}/${component_id}/individual_data_info`;
                var params = {};

                return httpService.get(params, url);

            }

            function deleteIndividualData(patient_id, component_id) {
                var form = {};
                var url = `/data/${patient_id}/${component_id}/delete_individual_data`;
                return httpService.post(form, url);
            }

            function saveData(patient_id, component_id, form) {
                var url = `/data/${patient_id}/${component_id}/save_data`;
                return httpService.post(form, url);
            }

            function saveDataType(form) {
                var url = `/data/${form.patient_id}/${form.data_id}/save_data_type`;

                return httpService.post(form, url);
            }

            function deleteData(patient_id, data_id) {
                var form = {};
                var url = `/data/${patient_id}/${data_id}/delete_data`;
                return httpService.post(form, url);
            }

            /**
             * Update displayed graph type for each data type
             * @returns {*}
             */
            function updateGraphType(form) {
                var url = `/data/update_graph`;

                return httpService.post(form, url);
            }

            function generateChartData(observation) {
                var result = [];

                // Generate data point(s)
                _.map(observation.observation_components, function (item, key) {

                    result.push(_.pluck(item.observation_component_values, 'value_quantity'));
                });

                return result;
            }

            function generateChartLabel(observation) {
                if (observation.observation_components.length == 0)
                    return [];
                // Generate data point(s)
                return _.pluck(observation.observation_components[0].observation_component_values, 'date');
            }

            function generateChartSeries(observation) {
                if (observation.observation_components.length == 0)
                    return [];
                return _.pluck(observation.observation_components, 'name');
            }

            function generateMostRecentValue(observation) {
                var result = [];
                if (observation.observation_components.length == 0)
                    return result.toString();


                _.map(observation.observation_components, function (item, key) {
                    if (item.observation_component_values.length > 0) {
                        // The most recent value descendant sort. So first item will be most recent item
                        var valueQuantity = _.last(item.observation_component_values).value_quantity;
                        // result.push(valueQuantity);
                        // var quantity = item.observation_component_values[0].value_quantity;

                        // Round number if blood pressure
                        if ('blood pressure' == observation.name) {
                            valueQuantity = isNaN(valueQuantity) ? 0 : Math.round(parseFloat(valueQuantity));
                        }

                        if ('weight' == observation.name) {
                            valueQuantity = isNaN(valueQuantity) ? 0 : parseFloat(valueQuantity).toFixed(1);
                        }

                        if ('body temperature' == observation.name) {
                            valueQuantity = isNaN(valueQuantity) ? 0 : parseFloat(valueQuantity).toFixed(1);
                        }

                        if ('heart rate' == observation.name) {
                            valueQuantity = isNaN(valueQuantity) ? 0 : Math.round(parseFloat(valueQuantity));
                        }
                        result.push(valueQuantity);
                    }
                    else
                        result.push('');
                });

                return result.join(" / ");
            }

            function updateViewMode(viewMode, data) {
                var now = moment().utc();

                // TODO: It's should be limited from server side
                // Limiting data for the chart.
                switch (viewMode) {
                    case "Week":
                        var weekAgo = now.subtract(1, 'week');
                        var filter = _.filter(data, function (item) {
                            return moment(item.effective_datetime).isAfter(weekAgo);
                        });
                        return filter;

                        break;
                    case "Month":
                        var monthAgo = now.subtract(1, 'month');
                        var filter = _.filter(data, function (item) {
                            return moment(item.effective_datetime).isAfter(monthAgo);
                        });
                        return filter;
                        break;
                    case "Year":
                        var yearAgo = now.subtract(1, 'year');
                        var filter = _.filter(data, function (item) {
                            return moment(item.effective_datetime).isAfter(yearAgo);
                        });
                        return filter;
                        break;
                    case "All":
                    default:
                        return data;
                        break;
                }
            }

            function getValueCount(data) {
                var now = moment().utc();
                var yearAgo = now.subtract(1, 'year');
                var count = 0;

                _.each(data.observation_components, function (component, key, list) {
                    var filter = _.filter(component.observation_component_values, function (item) {
                        return moment(item.created_on).isAfter(yearAgo);
                    });
                    count += filter.length;
                });

                return count;
            }

            function generateMostCommonData(datas) {
                var mostCommonData = _.sortBy(datas, function (data) {
                    var now = moment().utc();
                    var yearAgo = now.subtract(1, 'year');
                    var count = 0;

                    _.each(data.observation_components, function (component, key, list) {
                        var filter = _.filter(component.observation_component_values, function (item) {
                            return moment(item.created_on).isAfter(yearAgo);
                        });
                        count += filter.length;
                    });

                    return count;
                });

                mostCommonData = _.last(mostCommonData, 3);
                var lastRecentData = datas[0];

                if (!_.contains(_.pluck(mostCommonData, "id"), lastRecentData.id)) {
                    mostCommonData.push(lastRecentData);
                }

                return _.last(mostCommonData, 3);
            }

            /**
             * Request to delete multiple observation component value
             * TODO: Implement detail here
             * @param patientId
             * @param idArray
             */
            function deleteComponentValues(patientId, idArray) {
                return $http.delete(`/data/${patientId}/delete`, {
                    data: {
                        component_values: idArray
                    }
                });
            }
        });

})();