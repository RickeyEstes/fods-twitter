angular.module('app.directives')

.directive('leaflet', [
  function () {
    return {
      restrict: 'EA',
      replace: true,
      scope: {
        callback: "="
      },
      template: '<div></div>',
      link: function (scope, element, attributes) {
        var map = L.map(element[0], {
          // center: [ 52.163198, 5.4 ],
      		// maxZoom: 19,
      		// zoom: 8,
      		// minZoom: 8,
      		attributionControl:false,
      		doubleClickZoom: true,
          // maxBounds: [ [49.56797785892715,0.17578125],[55.15376626853556,10.52490234375]]
        });

        new L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
          maxZoom: 24,
          maxNativeZoom:20,
          attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy;<a href="https://carto.com/attribution">CARTO</a>'
        }).addTo(map);

        scope.callback(map);
      }
    };
  }
]);
