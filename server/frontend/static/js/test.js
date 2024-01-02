

function run_tests() {

    $('#go-button').prop('disabled', true);

    // Random selection of 10 problems from different domains.
    var PIDs = {1:8, 2:2352, 3:1809, 4:2703, 5:1116, 6:4399, 7:211, 8:4436, 9:818, 10:2487};

    // Want to call each test one after another.
    var cb = function(resp) {show_result('test10', resp)};
    for (var i=Object.keys(PIDs).length-1; i>=1; i--) {
        // We need to wrap in an anonymous function so the index is evaluated
        cb = (function(ind, cb) {
            return function(resp) {
                show_result('test'+ind, resp);
                solve_and_validate(PIDs[ind+1], cb);
            };
        })(i, cb);
    }

    solve_and_validate(PIDs[1], cb);
}

function show_result(lid, resp) {
    console.log(resp);
    if (resp.result.val_status === "valid")
        $('#'+lid).append("<strong>Ok!</strong>");
    else
        $('#'+lid).append("<strong>Failed: "+resp.result.val_status+"</strong>");
}

function solve_and_validate(pid, cb) {
    query('solve-and-validate', {probID:pid}, cb);
}

function query(qs, params, cb) {
    var SOLVER_URL = '/';

    $.ajax({
        url         : SOLVER_URL + qs,
        type        : 'POST',
        contentType : 'application/json',
        data        : JSON.stringify(params)
    }).done(cb);

}

