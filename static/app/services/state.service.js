angular.module('app.services')

.factory('StateService', function($http) {

  var factory = {

  }

  factory.getStates = function() {
    return $http
      .get('/api/getStates')
      .then(function(response) {
        return response.data.result;
      });
  };

  factory.getAllHashtags = function() {
    return $http
      .get('/api/getHashtags')
      .then(function(response) {
        return response.data.result;
      });
  };

  factory.getHashtags = function(state) {
    return $http
      .get('/api/getHashtags/' + state)
      .then(function(response) {
        return response.data.result;
      });
  };

  factory.getAllPreferences = function() {
    return $http
      .get('/api/getPreference')
      .then(function(response) {
        return response.data.result;
      });
  };

  factory.getPreference = function(state) {
    return $http
      .get('/api/getPreference/' + state)
      .then(function(response) {
        return response.data.result;
      });
  };

  return factory;
});
