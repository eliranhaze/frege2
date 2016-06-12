/**
 * Main controller.
 * 
 * Fixes:
 * - After getting a wrong answer, deleting it and submitting an empty answer, warning isn't shown.
 * 
 * Ideas:
 * - Explanations for every question - tell why it is right or wrong.
 * - How will the TA see their students results? Maybe only global results and not according to groups.
 * - Statistics - how many wrong answers, etc. per question and chapter, etc.
 * - Build a larger database of questions and each semester (or even each student) will get a subset of questions,
 *   which, of course, can be sliced by difficulty.
 * - Maybe reveal correctness of answers only when done answering (clicking done), so the student doesn't just try
 *   (for example) all 4 options until they get it right. But then again, they could just click 'done' after every question.
 *   So maybe 'done' will be allowed after answering most (or all) of the questions? Obviously in deduction questions it
 *   has to be different because they might not solve it at all, but then again-again, I could add a 'skip' button for
 *   that purpose. Also in formulations questions syntax has to be checked before moving on, I don't want them to find 
 *   out the syntax was wrong only at the end.
 * - For valid forumlae questions (there are only a few, but still) - a random valid/invalid formula generator.
 *   Maybe the same even for truth table questions.
 *   Maybe the same for formulations questions (!!!) !!! Where the teacher inputs hebrew sentences and all kinds
 *   of complex sentences are forms, using known connective keywords.
 *   And of course, do you see it coming?, maybe also for dedutions questions (!!!!).
 * - Practice mode, with generated exercises.
 * - User selected theme/background.
 * - Write chapter number somewhere on page.
 * - Keyboard events: arrows to change questions, enter to submit, etc.
 * - New question kind: value-giving.
 */

var app = angular.module('myApp', []);
app.controller('qCtrl', function($scope, $http) {
	var selectedChapter = 2 // User selected chapter will be here.
	var data = 'chapter=' + selectedChapter
	$http.post("http://localhost:8080/Logicore/LogicoreServlet", data).success(
			function(response) {
				// This is called last (only when (async) post-request returns).
				$scope.questions = response.questions;
				// Change to the first question.
				$scope.change();
			});
	/* *************** */
	/* Scope variables */
	/* *************** */
	$scope.i = 0;
	$scope.isCorrect = null;
	$scope.emptyAns = false;
	$scope.corrects = 0;
	/* ***************** */
	/* General functions */
	/* ***************** */
	$scope.q = function() {
		if ($scope.questions)
			return $scope.questions[$scope.i];
	};
	$scope.change = function() {
		$scope.isCorrect = null;
		$scope.emptyAns = false;
		$scope.userAnswer = null;
		$scope.handleTheTruth();
	};
	$scope.next = function() {
		var found = false;
		var nextWrong = null;
		var current = $scope.i;
		var i = current;
		while (!found) {
			i = (i + 1) % $scope.questions.length;
			if (i === current) {
				break;
			}
			if (typeof $scope.questions[i].correct === 'undefined') {
				found = true;
				break;
			}
			if (nextWrong === null && !$scope.questions[i].correct) {
				nextWrong = i;
			}
		}
		if (found) {
			$scope.go(i);
		} else if (nextWrong !== null){
			$scope.go(nextWrong);
		} else {
			$scope.go(($scope.i + 1) % $scope.questions.length);
		}
	};
	$scope.prev = function() {
		if ($scope.i == 0) {
			$scope.i = $scope.questions.length - 1;
		} else {
			$scope.i = ($scope.i - 1) % $scope.questions.length;
		}
		$scope.change();
	};
	$scope.go = function(i) {
		$scope.i = i
		$scope.change()
	};
	$scope.getPageClass = function(i) {
		if ($scope.i === i) {
			return ''
		}
		var correct = $scope.questions[i].correct
		if (typeof correct === 'undefined') {
			return ''
		}
		if (correct) {
			return 'alert-success'
		} else {
			return 'alert-danger'
		}
	};
	$scope.answered = function() {
		$scope.questions[$scope.i].correct = $scope.isCorrect;
		$scope.corrects = 0;
		for (var i = 0; i < $scope.questions.length; i++) {
			if ($scope.questions[i].correct) {
				$scope.corrects++;
			}
		}
	};
	/* *************** */
	/* Choice question */
	/* *************** */
	$scope.choose = function(choice) {
		$scope.isCorrect = ($scope.questions[$scope.i].correctChoice == choice + 1);
		$scope.answered();
	};
	/* ************* */
	/* Open question */
	/* ************* */
	$scope.answer = function(ans) {
		if (!ans) {
			$scope.emptyAns = true;
			$scope.isCorrect = null;
			return;
		}
		$scope.emptyAns = false;
		var answers = $scope.questions[$scope.i].answers;
		for (i = 0; i < answers.length; i++) {
			if (ans === answers[i]) {
				$scope.isCorrect = true;
				$scope.answered();
				return;
			}
		}
		$scope.isCorrect = false;
		$scope.answered();
	};
	/* ************ */
	/* Truth Tables */
	/* ************ */
	$scope.handleTheTruth = function() {
		if ($scope.questions) {
			var q = $scope.questions[$scope.i];
			if (typeof q.tt === 'undefined') {
				q.tt = new TruthTable(new Formula(q.formula));
			}
		}
	};
	$scope.selectTruth = function(row, col, value) {
		var q = $scope.questions[$scope.i];
		q.tt.select(row, col, value);
	};
	$scope.checkTruth = function() {
		var q = $scope.questions[$scope.i];
		var correct = q.tt.isCorrect();
		$scope.isCorrect = correct;
		if (correct === null) {
			$scope.emptyAns = true;
			return;
		}
		$scope.emptyAns = false;
		$scope.answered();
	};
	$scope.clearTruth = function() {
		var q = $scope.questions[$scope.i];
		q.tt.clearSelections();
		$scope.isCorrect = null;
		$scope.emptyAns = false;
	};
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