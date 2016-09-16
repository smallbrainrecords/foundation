(function () {

    'use strict';

    angular.module('ManagerApp').service('dataService',
        function ($http, $q, $cookies, httpService) {

            this.csrf_token = function () {

                var token = $cookies.csrftoken;
                return token;
            };

            this.fetchDataInfo = function (data_id) {
                var url = "/data/" + data_id + "/info";
                var params = {};

                return httpService.get(params, url);

            };

            this.fetchPinToProblem = function (data_id) {
                var url = "/data/" + data_id + "/get_pins";
                var params = {};

                return httpService.get(params, url);

            };

            this.dataPinToProblem = function (patient_id, form) {
                var url = '/data/' + patient_id + '/pin_to_problem';
                return httpService.post(form, url);
            };

            this.addData = function (patient_id, component_id, form) {
                var url = '/data/' + patient_id + '/' + component_id + '/add_new_data';
                return httpService.post(form, url);
            };

            this.fetchIndividualDataInfo = function (patient_id, component_id) {
                var url = "/data/" + patient_id + "/" + component_id + "/individual_data_info";
                var params = {};

                return httpService.get(params, url);

            };

            this.deleteIndividualData = function (patient_id, component_id) {
                var form = {};
                var url = "/data/" + patient_id + "/" + component_id + "/delete_individual_data";
                return httpService.post(form, url);
            };

            this.saveData = function (patient_id, component_id, form) {
                var url = '/data/' + patient_id + '/' + component_id + '/save_data';
                return httpService.post(form, url);
            };

            this.saveDataType = function (form) {
                var url = '/data/' + form.patient_id + '/' + form.data_id + '/save_data_type';

                return httpService.post(form, url);
            };

            this.deleteData = function (patient_id, data_id) {
                var form = {};
                var url = "/data/" + patient_id + "/" + data_id + "/delete_data";
                return httpService.post(form, url);
            };

            /**
             * Update displayed graph type for each data type
             * @returns {*}
             */
            this.updateGraphType = function (form) {
                var url = '/data/update_graph';

                return httpService.post(form, url);
            };


            this.generateChartData = function (observation) {
                var result = [];

                // Generate data point(s)
                _.map(observation.observation_components, function (item, key) {

                    result.push(_.pluck(item.observation_component_values, 'value_quantity'));
                });

                return result;
            };

            this.generateChartLabel = function (observation) {
                if (observation.observation_components.length == 0)
                    return [];
                // Generate data point(s)
                return _.pluck(observation.observation_components[0].observation_component_values, 'date');
            };

            this.generateChartSeries = function (observation) {
                if (observation.observation_components.length == 0)
                    return [];
                return _.pluck(observation.observation_components, 'name');
            };

            this.generateMostRecentValue = function (observation) {
                var result = [];
                if (observation.observation_components.length == 0)
                    return result.toString();


                _.map(observation.observation_components, function (item, key) {
                    if (item.observation_component_values.length > 0) {
                        // The most recent value descendant sort. So first item will be most recent item
                        var valueQuantity = _.last(item.observation_component_values).value_quantity;
                        result.push(valueQuantity);
                        // var quantity = item.observation_component_values[0].value_quantity;

                        // Round number if blood pressure
                        if (observation.name == 'blood pressure') {
                            valueQuantity = Math.round(quantity);
                        }
                        result.push(quantity);
                    }
                    else 
                        result.push('');
                });

                return result.join(" / ");
            };

            this.updateViewMode = function (viewMode, data) {
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
            };

            this.getValueCount = function (data) {
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
            };

            this.generateMostCommonData = function(datas) {
                var mostCommonData = _.sortBy(datas, function(data){
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
            };
        });

})();