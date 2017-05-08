'use strict';
(function() {

    /**
     * Directive that executes an expression when the element it is applied to gets
     * an `escape` keydown event.
     */
    var myTools = angular.module('myTools', []).config(function($httpProvider){
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });










myTools.directive('fileModel', ['$parse', function ($parse) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var model = $parse(attrs.fileModel);
            
            
            element.bind('change', function(){
                scope.$apply(function(){
                    var modelSetter = model.assign;
                    modelSetter(scope, element[0].files[0]);
                });
            });
        }
    };
}]);


})();