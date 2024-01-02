planningapi = function() {
  var API_URL = "//api.planning.domains/json/classical/";
  var SOLVER_URL = "/";
  var TIMEOUT = 12000; // 12s

  var collections;
  var domains;
  var problems;
  var solving;

  function progressbar_update(start, bar) {
    var t = (new Date()).getTime() - start.getTime();
    var p = Math.round((t/TIMEOUT)*100);
    if(solving && p < 100) {
      bar.css('width', p + "%");
      bar.children('span').html(p + "%");
      setTimeout(progressbar_update, 100, start, bar);
    }
  }

  function progressbar_init() {
    var progress_div = $("#solving .progress");
    var bar = $("#solving .progress .progress-bar");
    var btn = $("#solving .btn");

    bar.removeClass();
    bar.addClass("progress-bar progress-bar-success progress-bar-striped active");
    bar.css("width", "0%");
    progress_div.css('visibility', 'visible');

    solving = true;
    setTimeout(progressbar_update, 100, new Date(), bar);
  }

  function progressbar_error() {
    var bar = $("#solving .progress .progress-bar");
    solving = false;
    bar.removeClass();
    bar.addClass("progress-bar progress-bar-danger");
    bar.css("width", "100%");
  }

  function progressbar_success() {
    var bar = $("#solving .progress .progress-bar");
    solving = false;
    bar.removeClass();
    bar.addClass("progress-bar progress-bar-success");
    bar.css("width", "100%");
  }

  function solve_enable() {
    $("#solving .btn").prop('disabled', false);
  }

  function solve_disable() {
    $("#solving .btn").prop('disabled', true);
  }

  function solve() {
    var prob_index = $("#problems option:selected").val();
    var domain_text;
    var pb_text;

    $("#solution").html("");
    $("#planner_output").html("");
    progressbar_init();

    $.ajax({
      url         : SOLVER_URL + "solve",
      type        : "POST",
      contentType : 'application/json',
      data        : JSON.stringify({"domain" : problems[prob_index].domain_url,
                                   "problem": problems[prob_index].problem_url,
                                   "is_url": true
                    })
    }).done(function (res) {
      console.log("Server responce:");
      console.log(res);
      if (res['status'] === 'ok') {
        progressbar_success();

        var items = [];
        $.each(res.result.plan, function(index, val) {
          if (res.result.type === 'full')
            items.push("<li>" + val.name + "</li>");
          else
            items.push("<li>" + val + "</li>");
        });
        $("#solution").html("<ol>" + items.join("") + "</ol>");
        $("#planner_output").html("<pre>" + res.result.output.replace("\n", "<br/>") + "</pre>");

      } else {
        progressbar_error();
        if (typeof res.result.killed != 'undefined')
          $("#planner_output").html("<pre>Planner Timed Out</pre>");
        else if (typeof res.result.error != 'undefined')
          $("#planner_output").html("<pre>" + res.result.error.replace("\n", "<br/>") + "</pre>");
        else
          $("#planner_output").html("<pre>" + JSON.stringify(res.result, null, 3) + "</pre>");
      }
    }).fail(function (jqxhr, error) {
      progressbar_error();
      $("#planner_output").html("<pre>" + error + "</pre>");
    });

    return false;
  }

  function collection_change() {
    $("#domains").html("");

    var col_index = $("#collections option:selected").val();
    var sel_domains = null;

    var description = "";
    if(col_index >= 0) {
      description = collections[col_index].description;
      sel_domains = JSON.parse(collections[col_index].domain_set);
    }
    $("#col_desc").html(description);

    var items = [];
    $.each(domains, function(index, val) {
      if(col_index < 0 || sel_domains.indexOf(val.domain_id) > -1) {
        items.push("<option value=" + index + ">(" + val.domain_id + ") " + val.domain_name + "</option>");
      }
    });
    $("#domains").html(items.join(""));

    domain_change();
  }

  function domain_change() {
    solve_disable();
    $("#problems").html("");

    var dom_index = $("#domains option:selected").val();
    $("#dom_desc").html(domains[dom_index].description.replace(/\n/g, '<br>'));

    $.getJSON(API_URL + "problems/" + domains[dom_index].domain_id, function(data) {
      data.result.sort(function(a,b) { return a.problem.toLowerCase() > b.problem.toLowerCase(); });
      problems = data.result;
      var items = [];
      $.each(problems, function(index, val) {
        items.push("<option value = " + index + ">" + val.problem + "</option>");
      });
      $("#problems").html(items.join(""));
      problem_change();
      solve_enable();
    });
  }

  function problem_change() {
    var prob_index = $("#problems option:selected").val();
    var ub = problems[prob_index].upper_bound;
    var lb = problems[prob_index].lower_bound;
    $("#prob_desc").html(
      "<ul>" +
        "<li>Upper bound: " + (ub == null ? "unknown" : ub) + "</li>" +
        "<li>Lower bound: " + (lb == null ? "unknown" : lb) + "</li>" +
      "</ul>"
    );
  }

  function _init() {
    $.getJSON(API_URL + "collections", function(data) {
      data.result.sort(function(a,b) { return a.collection_name.toLowerCase() > b.collection_name.toLowerCase(); });
      collections = data.result;
      var items = ["<option value=\"-1\" selected>All domains</option>"];
      $.each(collections, function(index, val) {
        items.push("<option value = " + index + ">" + val.collection_name + "</option>");
      });
      $("#collections").html(items.join(""));
    });

    $.getJSON(API_URL + "domains", function(data) {
      data.result.sort(function(a,b) { return a.domain_name.toLowerCase() > b.domain_name.toLowerCase(); })
      domains = data.result;
      var items = [];
      $.each(domains, function(index, val) {
        items.push("<option value=" + index + ">(" + val.domain_name + ") " + val.domain_name + "</option>");
      });
      $("#domains").html(items.join(""));
      $("#collections").change(collection_change);
      $("#domains").change(domain_change);
      $("#problems").change(problem_change);
      domain_change();
    });

    $("#solving .btn").click(solve);
  }

  return {
    init : _init,
  }
}();

