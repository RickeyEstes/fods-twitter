  angular.module('app.routes')

  .config(function($stateProvider, $locationProvider, $urlRouterProvider) {

    $locationProvider.html5Mode(true);

    $stateProvider

    .state('home', {
      url: '/',
      templateUrl: '/static/app/views/home.view.html',
      controller: 'HomeController',
      resolve: {
        stateList: function(StateService) {
          return StateService.getStates();
        },
        hashtagList: function($http) {
          return $http
            .get('/static/data/top_hashtags.csv')
            .then(function(response) {
              var text = response.data
               // split content based on new line
              var textLines = text.split(/\r\n|\n/);
              var headers = textLines[0].split(',');
              var lines = [];

              for ( var i = 0; i < textLines.length; i++) {
                 // split content based on comma
                 var data = textLines[i].split(',');
                 if (data.length == headers.length) {
                     var tarr = [];
                     for ( var j = 0; j < headers.length; j++) {
                         tarr.push(data[j]);
                     }
                     lines.push(tarr);
                 }
              }
              return lines
            });
        }
      }
    })

    $urlRouterProvider.otherwise('/');
  });
