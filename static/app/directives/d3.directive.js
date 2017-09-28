angular.module('app.directives')

.directive('histogram', function(d3Service, $state, $window, $rootScope) {
  return {
    restrict: 'EA',
    scope: {
      data: '=',
      zero: '=',
      theme: '='
    },
    link: function(scope, element, attrs) {
      d3Service.d3().then(function(d3) {
        // Set margins
        var margin = { top: 20, right: 20, bottom: 20, left: 50 };
        var width = parseInt(d3.select('.tw-segment-histogram').style('width'), 10) - margin.left - margin.right;
        var height = parseInt(d3.select('.tw-segment-histogram').style('height'), 10) - margin.top - margin.bottom;

        var x = d3.scale.ordinal().rangeRoundBands([0, width], .05);
        var y = d3.scale.linear().range([height, 0]);

        var xAxis = d3.svg.axis()
          .scale(x)
          .orient("bottom")

        var yAxis = d3.svg.axis()
          .scale(y)
          .orient("left")
          .ticks(10);

        var svg = d3.select(element[0]).append("svg")
          .attr("width", width + margin.left + margin.right)
          .attr("height", height + margin.top + margin.bottom)
        .append("g")
          .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");

        // Browser onresize event
        window.onresize = function() {
          scope.$apply();
        };

        window.addEventListener('resize', scope.render);

        // Watch for resize event
        scope.$watch(function() {
          return angular.element($window)[0].innerWidth;
        }, function(newW) {
          // Workaround, need proper responsiveness
          width = parseInt(d3.select('.tw-segment-histogram').style('width'), 10) - margin.left - margin.right;
          height = parseInt(d3.select('.tw-segment-histogram').style('height'), 10) - margin.top - margin.bottom;
          svg.attr('width', width).attr('height', height);

          scope.render(scope.data);
        });

        // Watch for data change
        scope.$watch('data', function(newData, oldData) {
          if (newData !== oldData) {
            scope.render(scope.data);
          }
        });

        scope.render = function(data) {
          //Remove previous render
          svg.selectAll('*').remove();
          if (!data) {
            return
          }

          data.sort(function(a, b) { return a._id - b._id; });
          data.forEach(function(d) {
            d._id = +d._id;
            d.count = +d.count;
          });

          var scale = []
          for (var i = -5; i <= 5; i++) {
            scale.push(i)
          }

          if (scope.zero == false) {
            data = data.filter(function(d) {
              if (d._id != 0) {
                return true
              } else {
                return false
              }
            });

            scale = scale.filter(function(d) {
              if (d != 0) {
                return true
              } else {
                return false
              }
            });
          }

          x.domain(scale);
          y.domain([0, d3.max(data, function(d) { return d.count; })]);

          // add axis
          svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
          .selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", "-.55em")
            .attr("transform", "rotate(-90)" );

          svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
          .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 5)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Frequency");

          // Add bar chart
          svg.selectAll("bar")
            .data(data)
          .enter().append("rect")
            .attr("class", function(d) {
              if (attrs.theme == "candidate") {
                if (d._id < 0) {
                  return "bar-hillary"
                } else if (d._id > 0) {
                  return "bar-trump"
                }
              } else {
                return "bar"
              }
            })
            .attr("x", function(d) { return x(d._id); })
            .attr("width", x.rangeBand())
            .attr("y", function(d) { return y(d.count); })
            .attr("height", function(d) { return height - y(d.count); });
        };

      });
    }
  };
})
