
var PAS_MODEL = `
<!-- Choose Files Modal -->
<div class="modal fade" id="chooseFilesPASModel" tabindex="-1" role="dialog" aria-labelledby="chooseFilesModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title" style="display:inline" id="chooseFilesModalLabel">Compute plan</h4>
      </div>
      <div class="modal-body">
        <form class="form-horizontal left" role="form">
          <div class="form-group">
            <label for="domainPASSelection" class="col-sm-4 control-label">Domain</label>
            <div class="col-sm-8">
              <select id="domainPASSelection" class="form-control file-selection">
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="problemPASSelection" class="col-sm-4 control-label">Problem</label>
            <div class="col-sm-8">
              <select id="problemPASSelection" class="form-control file-selection">
              </select>
            </div>
          </div>     
          <div class="form-group">
          <label for="solverPASSelection" class="col-sm-4 control-label">Solver</label>
          <div class="col-sm-8">
            <select id="solverPASSelection" class="form-control file-selection">
            <option value="lama-first">Lama-first</option>
            <option value="lama">Lama</option>
            </select>
          </div>
        </div>    
        </form>

        <button id="filesChosenButton" class="btn-lg btn-success" type="button" onclick="filesChosen()">Plan</button>
    


        <div class="form-group" style="display:inline-block">
            


        <div id="plannerURLInput" class="input-group">
          <span class="input-group-addon" id="customPlannerLabel">Custom Planner URL</span>
          <input id="plannerPASURL" type="text" class="form-control" aria-describedby="customPlannerLabel" placeholder="http://solver.planning.domains/solve">
        </div>
          
      </div>
      <br/>

      <div class="modal-footer"  >
        <button type="button" class="btn btn-default"  data-dismiss="modal">Cancel</button>
      </div>
    </div>
  </div>
</div>
`

// To Do
// function getSolverManifest(){
//   var solverName = $('#solverPASSelection').find(':selected').val();
//   $.ajax( {url: window.PASURL +solverName+ "/solve",
//   type: "GET",
//   contentType: 'application/json'
// })
// .done(function (res) {

//      if (res['status'] === 'ok') {
//          window.toastr.success('Plan found!');
//      } else {
//          window.toastr.error('Planning failed.');
//      }
//      console.log(res)

//     //  showPlan(res);

//  }).fail(function (res) {
//      window.toastr.error('Error: Malformed URL?');
//  });
// }



function getPlan(taskID) {

  var i = 1;                  //  set your counter to 1

  setTimeout(function () {   //  call a 3s setTimeout when the loop is called
    $.ajax({
      url: window.PASURL + taskID,
      type: "POST",
      contentType: 'application/json',
      data: JSON.stringify({ "adaptor": "planning_editor_adaptor" })
    })
      .done(function (res) {

        if (res['status'] === 'ok') {
          window.toastr.success('Plan is ready');
          showPlan(res)
        } else if (res['status'] === 'error') {
          window.toastr.error('Planning failed.');
          showPlan(res)
        }
        else {
          i++;
          if (i < 3) {
            getPlan(taskID);
          }
          window.toastr.info('Solving in progress, will check again in 10S');
        }

      }).fail(function (res) {
        window.toastr.error('Error: Malformed URL? ' + window.PASURL + taskID);
      });
  }, 11000)
}


// function to run animation of resultant output in iframe
function runPAS() {
  var domText = window.ace.edit($('#domainPASSelection').find(':selected').val()).getSession().getValue();
  var probText = window.ace.edit($('#problemPASSelection').find(':selected').val()).getSession().getValue();
  var solverName = $('#solverPASSelection').find(':selected').val();
  window.toastr.info('Running remote planner...');

  $('#chooseFilesPASModel').modal('toggle');

  // Send task to the solver
  $.ajax({
    url: window.PASURL + "/package/" + solverName + "/solve",
    type: "POST",
    contentType: 'application/json',
    data: JSON.stringify({ "domain": domText, "problem": probText })
  })
    .done(function (res) {
      if ("result" in res) {
        window.toastr.success('Task Initiated!');
        // Check the plan result
        getPlan(res["result"])
      }

    }).fail(function (res) {
      window.toastr.error('Error: Malformed URL?');
    });

}


function choosePASFiles(type) {

  window.action_type = type
  window.file_choosers[type].showChoice();

  var domain_option_list = "";
  var problem_option_list = "";
  var unknown_option_list = "";
  var hr_line = "<option disabled=\"disabled\">---------</option>\n";
  var setDom = false;
  var setProb = false;


  for (var i = 0; i < window.pddl_files.length; i++) {
    if ($.inArray(window.pddl_files[i], window.closed_editors) == -1) {
      if (window.pddl_files[i] == window.last_domain)
        setDom = true;
      if (window.pddl_files[i] == window.last_problem)
        setProb = true;

      var option = "<option value=\"" + window.pddl_files[i] + "\">" + $('#tab-' + window.pddl_files[i]).text() + "</option>\n";
      var file_text = window.ace.edit(window.pddl_files[i]).getSession().getValue();
      if (file_text.indexOf('(domain') !== -1)
        domain_option_list += option;
      else if (file_text.indexOf('(problem') !== -1)
        problem_option_list += option;
      else
        unknown_option_list += option;
    }
  }

  var domain_list = domain_option_list + hr_line + unknown_option_list + hr_line + problem_option_list;
  var problem_list = problem_option_list + hr_line + unknown_option_list + hr_line + domain_option_list;
  $('#domainPASSelection').html(domain_list);
  $('#problemPASSelection').html(problem_list);
  if (setDom)
    $('#domainPASSelection').val(window.last_domain);
  if (setProb)
    $('#problemPASSelection').val(window.last_problem);
  $('#chooseFilesPASModel').modal('toggle');
}

define(function () {

  // Use this as the default solver url
  window.PASURL = "http://localhost:5001";

  // Use a flag to only insert styles once
  window.PASSolverStyled = false;

  return {

    name: "Planning as service",
    author: "Nir Lipovetzky, Yi Ding",
    email: "nir.lipovetzky@unimelb.edu.au",
    description: "Solve problem with various solvers",

    initialize: function () {
      // This will be called whenever the plugin is loaded or enabled

      // add menu item on the top menu
      window.add_menu_button('PlanningAsService', 'pasMenuItem', 'glyphicon-dashboard', "choosePASFiles('PlanningAsService')");
      window.register_file_chooser('PlanningAsService',
        {
          showChoice: function () {

            window.action_type = 'PlanningAsService'
            $('#plannerPASURL').val(window.PASURL);
          },
          selectChoice: runPAS
        });

      if (!(window.PASSolverStyled)) {
        $('body').append(PAS_MODEL);


        window.PASSolverStyled = true;
      }

    },

    disable: function () {
      // This is called whenever the plugin is disabled
      window.remove_menu_button('pasMenuItem');
    },

    save: function () {
      // Used to save the plugin settings for later
      return { PASURL: window.PASURL };
    },

    load: function (settings) {
      // Restore the plugin settings from a previous save call
      window.PASURL = settings['PASURL'];
    }

  };
});