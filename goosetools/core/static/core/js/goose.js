GooseJs = function () {
    function filterColumn(column, val, include_partial_matches, empty_filter_name){
        search_regex = include_partial_matches ? val : `^${val}$`;

        if(val && empty_filter_name && empty_filter_name === val){
            search_regex = `^$`;
        }

        column
            .search(val ? search_regex : '', true, false)
            .draw();
    }
    function dataTableColumnFilterInit(settings, json) {
        table = settings.oInstance.api();
        const columns = table.settings().init().columns;
        this.api().columns().every(function (index) {
            const column_info = columns[index]
            var column = this;
            if (column_info["give_filter"] || column_info["filter_values"]) {
                var select = $(`<label class="black-text">${column_info["title"]}</label>`)
                    .appendTo($(column.header()).empty())

                function filter_column() {
                    var val = $.fn.dataTable.util.escapeRegex(
                        $(this).val()
                    );
                    filterColumn(column, val, column_info["include_partial_matches"], column_info["empty_filter_name"]);
                }
                var select = $('<select class="browser-default"><option value=""></option></select>')
                    .appendTo($(column.header()))
                    .on('change', filter_column
                    );

                if (column_info["filter_values"]) {
                    if(column_info["empty_filter_name"]){
                        if (column_info["initial_filter_value"] === column_info["empty_filter_name"]) {
                            select.append('<option value="' + column_info["empty_filter_name"] + '" selected>' + column_info["empty_filter_name"] + '</option>')
                            filterColumn(column, column_info["empty_filter_name"], column_info["include_partial_matches"], column_info["empty_filter_name"]);
                        } else {
                            select.append('<option value="' + column_info["empty_filter_name"] + '">' + column_info["empty_filter_name"] + '</option>')
                        }
                    }
                    column_info["filter_values"].forEach(function (d) {
                        if (column_info["initial_filter_value"] === d) {
                            select.append('<option value="' + d + '" selected>' + d + '</option>')
                            filterColumn(column, d, column_info["include_partial_matches"], column_info["empty_filter_name"]);
                        } else {
                            select.append('<option value="' + d + '">' + d + '</option>')
                        }
                    });

                } else {
                    column.data().unique().sort().each(function (d, j) {
                        if (column_info["initial_filter_value"] === d) {
                            select.append('<option value="' + d + '" selected>' + d + '</option>')
                            filterColumn(column, d, column_info["include_partial_matches"], column_info["empty_filter_name"]);
                        } else {
                            select.append('<option value="' + d + '">' + d + '</option>')
                        }
                    });
                }

            }
        });
    }
    function json_django_request(url) {
        const csrftoken = Cookies.get('csrftoken');
        return new Request(
            url,
            {
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            }
        );
    }


    const page_data = JSON.parse(document.getElementById('page-data').textContent);
    return {
        "datatable": function datatable(column_init_func) {
            const user_data_table_config = column_init_func(page_data);
            const goose_data_table_config = {
                dom: 'Bfrtip',
                pageLength: 50,
                responsive: true,
                ajax: {
                    url: page_data["ajax_url"],
                    dataSrc: '',
                    error: function (xhr, error, code) {
                        console.log(xhr);
                        console.log(code);
                        console.log(error);
                        alert("An error occured getting the data. Please contact @thejanitor on discord.");
                    }
                },
                buttons: [
                    'excelHtml5',
                    'csvHtml5',
                ],
                initComplete: dataTableColumnFilterInit
            }
            const merged_data_table_config = [user_data_table_config, goose_data_table_config].reduce((acc, el) => {
                for (let key in el) {
                    if(Array.isArray(el[key])){
                        if(acc[key]){
                            acc[key] = acc[key].concat(el[key]);
                        } else {
                            acc[key] = el[key];
                        }
                    } else if (typeof el[key] === 'object' && el[key] !== null){
                        acc[key] = { ...acc[key], ...el[key]};
                    } else {
                        acc[key] = el[key];
                    }
                };
                return acc;
                }, {})

            table = $('#datatable').DataTable(merged_data_table_config);
            return table;
        },
        "django_request": function django_request(url) {
            const csrftoken = Cookies.get('csrftoken');
            return new Request(
                url,
                { headers: { 'X-CSRFToken': csrftoken } }
            );
        },
        "json_django_request": json_django_request,
        putSubjectAction: function putSubjectAction(table, subject, action, api_url="api", success_callback=false) {
            return function () {
                const row = table.row($(this).parents('tr'));
                const id = row.data()['id'];
                const url = `${page_data["site_prefix"]}${api_url}/${subject}/${id}/${action}/`
                const request = json_django_request(url);
                fetch(request, {
                    method: 'PUT',
                    mode: 'same-origin'
                })
                    .then(response => response.json())
                    .then(response_data => {
                        row.data(response_data);
                        if(success_callback){
                            success_callback(response_data);
                        }
                        table.draw();
                    });

            }
        },
        numberWithCommas: function numberWithCommas(x) {
            var x = x.toString();
            var x = x.replace(/,/g, '');
            return x.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }

    };
};
