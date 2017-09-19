  angular.module('app.routes')

  .config(function($stateProvider, $urlRouterProvider) {

    $stateProvider

    .state('home', {
      url: '/home',
      templateUrl: '/static/app/views/home.view.html',
      controller: 'HomeController',
    })

    $urlRouterProvider.otherwise('/home');
  });
