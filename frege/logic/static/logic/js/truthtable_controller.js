/**
 */

var app = angular.module('myApp', []);
app.controller('qCtrl', function($scope, $http) {
    return true;
});

/* Utilities */

function newarray(len, initval) {
	var a = [];
	for (var i = 0; i < len; i++) {
		a.push(initval);
	}
	return a;
}

function new2darray(rows, cols, initval) {
	var a = [];
	for (var i = 0; i < rows; i++) {
		var row = [];
		a.push(row);
		for (var j = 0; j < cols; j++) {
			row.push(initval);
		}
	}
	return a;
}

function initarray(a, initval) {
	for (var i = 0; i < a.length; i++) {
		a[i] = initval;
	}
}
