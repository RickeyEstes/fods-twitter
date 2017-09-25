angular.module('app.controllers')

.controller('HomeController', function(
  $scope, $location, $state, $timeout,
  stateList,
  StateService
) {

  $scope.selectedState = {
    name: 'United States'
  };

  $scope.fetchingHashtags = true;
  $scope.fetchingPreference = true
  StateService.getAllHashtags().then(function(response) {
    $scope.hashtags = response;
    $scope.fetchingHashtags = false;
  });

  StateService.getAllPreferences().then(function(response) {
    $scope.preferences = response;
    $scope.fetchingPreference = false;
  });

  $scope.selectState = function(state) {
    $timeout(function() {
      $scope.selectedState = state;
      $scope.fetchingHashtags = true;
      $scope.hashtags = []
      $scope.fetchingPreference = true
      $scope.preferences = []
      
      StateService.getHashtags(state.abbreviation).then(function(response) {
        $scope.hashtags = response;
        $scope.fetchingHashtags = false;
      });

      StateService.getPreference(state.abbreviation).then(function(response) {
        $scope.preferences = response;
        $scope.fetchingPreference = false;
      });
    });
  }

  $scope.map = function(map) {
    $scope.leaflet = map;

    $scope.geojsonLayer = L.layerGroup();
    $scope.geojsonLayer.addTo(map);

    // for (x in stateList) {
    //   console.log(stateList[x].name);
    // }

    $scope.geojson = L.geoJson(stateList, {
      style: function (feature) {
        return {
          color: '#333',
          weight: 2,
          fillOpacity: 0
        };
      },
      onEachFeature: function (feature, layer) {
        layer.on('mouseover', function(e) {
          layer.setStyle({
            color: 'rgb(22, 160, 133)',
            weight: 5
          })
        });
        layer.on('mouseout', function(e) {
          layer.setStyle({
            color: '#333',
            weight: 2
          })
        });
        layer.on('click', function(e) {
          // Determine if compare mode is on
          $scope.selectState(feature.properties)
        });
      }
    }).addTo($scope.geojsonLayer);

    map.fitBounds($scope.geojson.getBounds());

  }

});
