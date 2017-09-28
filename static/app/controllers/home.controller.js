angular.module('app.controllers')

.controller('HomeController', function(
  $scope, $location, $state, $timeout,
  stateList, hashtagList,
  StateService
) {

  $scope.selectedState = {
    name: 'United States'
  };

  $scope.showTopics = 'overall'

  $scope.getCandidate = function(hashtag) {
    hashtagIndex = hashtagList.map(function(hashtag) {
      return hashtag[0]
    }).indexOf(hashtag)

    if (hashtagIndex != -1) {
      var score = hashtagList[hashtagIndex][1]

      if (score == -1) {
        return 'tw-segment-list-hashtag-hillary'
      } else if (score == 1) {
        return 'tw-segment-list-hashtag-trump'
      }
    }


  };

  $scope.showPreference = function() {
    $scope.view = 'preference'
  }

  $scope.showSentiment = function(sentiment) {
    $scope.view = sentiment
  }

  $scope.getPreferenceColor = function(d) {
    return d > 0.15    ? '#bf3e2f' :
           d > 0.10    ? '#a56e61' :
           d > 0.05    ? '#8f827e' :
           d > 0       ? '#7f8c8d' :
           d > -0.05   ? '#738997' :
           d > -0.1    ? '#6086a4' :
                         '#2980b9' ;
  };

  $scope.getSentColor = function(d) {
    return d > 0.45    ? '#24ae5f' :
           d > 0.30    ? '#609e77' :
           d > 0.15    ? '#24ae5f' :
           d > 0       ? '#7f8c8d' :
           d > -0.15   ? '#8f827e' :
           d > -0.30   ? '#a56e61' :
                         '#bf3e2f' ;
  };

  $scope.fetchingHashtags = true;
  $scope.fetchingPreference = true
  $scope.fetchingSentiment = true;
  StateService.getAllHashtags().then(function(response) {
    $scope.hashtags = response;
    $scope.fetchingHashtags = false;
  });

  StateService.getAllPreferences().then(function(response) {
    $scope.preferences = response;
    $scope.fetchingPreference = false;
  });

  StateService.getAllSentiment().then(function(response) {
    $scope.sentiment = response;
    $scope.fetchingSentiment = false;
  });

  $scope.selectState = function(state) {
    $timeout(function() {
      $scope.selectedState = state;
      $scope.fetchingHashtags = true;
      $scope.hashtags = [];
      $scope.fetchingPreference = true
      $scope.preferences = [];
      $scope.fetchingSentiment = true;
      $scope.sentiment = [];

      StateService.getHashtags(state.abbreviation).then(function(response) {
        $scope.hashtags = response;
        $scope.fetchingHashtags = false;
      });

      StateService.getPreference(state.abbreviation).then(function(response) {
        $scope.preferences = response;
        $scope.fetchingPreference = false;
      });

      StateService.getSentiment(state.abbreviation).then(function(response) {
        $scope.sentiment = response;
        $scope.fetchingSentiment = false;
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
          fillOpacity: 0,
        };
      },
      onEachFeature: function (feature, layer) {

        $scope.$watch('view', function(value) {
          if (value == 'preference') {
            layer.setStyle({
              fillOpacity: 1,
              fillColor: $scope.getPreferenceColor(feature.properties.preference)
            });
          }

          if (value == 'sentOverall') {
            layer.setStyle({
              fillOpacity: 1,
              fillColor: $scope.getSentColor(feature.properties.sentiment.total)
            });
          }

          if (value == 'sentTrump') {
            layer.setStyle({
              fillOpacity: 1,
              fillColor: $scope.getSentColor(feature.properties.sentiment.trump)
            });
          }

          if (value == 'sentClinton') {
            layer.setStyle({
              fillOpacity: 1,
              fillColor: $scope.getSentColor(feature.properties.sentiment.clinton)
            });
          }

        })

        layer.on('mouseover', function(e) {
          layer.setStyle({
            color: 'rgb(22, 160, 133)',
            weight: 2
          })
        });
        layer.on('mouseout', function(e) {
          layer.setStyle({
            color: '#333',
            weight: 2
          })
        });
        layer.on('click', function(e) {
          $scope.selectState(feature.properties)
          console.log(feature.properties);
        });
      }
    }).addTo($scope.geojsonLayer);

    map.fitBounds($scope.geojson.getBounds());

  }

});
