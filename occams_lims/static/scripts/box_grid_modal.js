function fill_box_value(button){
  var modal_container = document.getElementById('modal-target'),
      // positions within button id example column[c]row[4]box[1]
      boxColumnPosition = 7,
      boxRowPosition = 13,
      boxStartPosition = 19,
      // replace_row being the row of the aliquot display grid
      replace_row = modal_container.dataset.target,
      idString = button.closest('td').id;
      targetBoxColumn = "#aliquot-" + replace_row + "-box_column"
      // target row being the box row
      targetBoxRow = "#aliquot-" + replace_row + "-box_row"
      targetBox = "#aliquot-" + replace_row + "-box"
      column = idString.charAt(boxColumnPosition);
      row = idString.charAt(boxRowPosition);
      boxEndPosition = (idString.length-1);
      box = (idString.substring(boxStartPosition, boxEndPosition));

  // replace the values of the target items
  $(targetBoxRow).val(row);
  $(targetBoxColumn).val(column);
  $(targetBox).val(box);
  $('#modal-target').modal('hide');
};

function fill_grid(data){
  jQuery.each(data, function() {
    var target_element = 'column[' + this.box_col + ']' +
                         'row[' + this.box_row +
                         ']box[' + this.box + ']',
        replace_value = this.abbr;
    document.getElementById(target_element)
            .innerHTML = replace_value;
  });
};


function build_grid(data) {
  // This function returns a table with labelled row/col grids for box fill

  // Find unique boxes from data to create tabs
  function unique_boxes(data) {
    var names = {};

    jQuery.each(data, function() {
      var box_name = this.box;
      if(!(box_name in names)) {
        names[box_name] = 1
      };
    });

    return (Object.keys(names));
  };

  // helper function to turn int into letter for LIMS box grid
  function rowIntToLetter(number){
    //97 is ASCII a
    var character = String.fromCharCode(97 + number);
    return character
  };

  function buildTable(idTag){
    var $topDiv = $('<div>').addClass('tab-pane').attr('id', idTag),
        $table = $( '<table>' ).addClass('table table-striped table-grid table-dimensional'),
        column_label = '<th></th>';

    //  Create rows/columns with buttons
    for(var i = 9; i > 0; i--) {
      row_label = '<th class="row align-middle">' + i.toString() + '</th>';

      row_append = '<tr class="align-middle" id=row-' + i.toString() + '>';
      row_append += row_label;

      for(var j = 0; j < 9; j++){
        if (i == 9) {
          column_label+='<th class="col">' + rowIntToLetter(j) + '</th>';
        }
        row_append+='<td id=column[' + rowIntToLetter(j) + ']' +
                    'row[' + i.toString() + ']' +
                    'box[' + idTag.toString() + ']>' +
                    '<button type=button onclick="fill_box_value(this)">' +
                    i.toString() + rowIntToLetter(j) + '</button></td>'
      }
      $table.append(row_append)
    }
    $table.append('<tfoot><tr>' + column_label + '</tr></tfoot>')
    $topDiv.append($table)
    return $topDiv
  };

  var box_names = unique_boxes(data),
      $navtabs = $('<ul>').addClass('nav nav-pills'),
      $tables = $('<div>').addClass('tab-content'),
      add_active = true;


  // Create tabs for each box and append grid tables
  jQuery.each(box_names, function() {
    $navtabs.append('<li role="presentation"><a href="#' +
                    this + '" data-toggle="tab">' + this + "</a></li>")
    $tables.append(buildTable(this));
    if (add_active === true){
      add_active = false;
      $navtabs.find("li").addClass('active');
      $tables.find("div").addClass('active');
    };
  });

  $navtabs.append($tables);
  return $navtabs;
}

