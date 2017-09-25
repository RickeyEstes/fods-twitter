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
      }
    })

    $urlRouterProvider.otherwise('/');
  });
