
$(function () {
    const page_data = JSON.parse(document.getElementById('page-data').textContent);
    Goose = GooseJs();
    table = Goose.datatable(function (page_data) {
        return {
            buttons: [
                {
                    text: 'Toggle Detail Columns',
                    action: function (e, dt, node, config) {
                        for (var i = 1; i < 9; i++) {
                            var column = dt.column(i);
                            column.visible(!column.visible());
                        }
                    }
                }
            ],
            order: [[4, "asc"]],
            columns: [
                { "data": "status", "title": "Status", "give_filter": true, "initial_filter_value": page_data["status_filter"] },
                {
                    "data": "from_user_display_name", "title": "Contract Info (Click for Details)",
                    render: function (data, type, row) {
                        function mad_make() {
                            is_sending_user = page_data["gooseuser_id"] === row["from_user"]
                            is_recieving_user = page_data["gooseuser_id"] === row["to_char_user_id"]
                            switch (row["status"]) {
                                case "requested":
                                    if (row['isk'] === 0) {
                                        return "Invalid Requested Contract for 0 ISK."
                                    } else if (row['isk'] > 0) {
                                        if (is_recieving_user) {
                                            return `You have requested that ${row['from_user_display_name']} sends you ${row['isk']} ISK to "${row['to_char_ingame_name']}" in-game`;
                                        } else {
                                            return `${row['to_char_display_name']} has requested you send ${row['isk']} ISK to their character "${row['to_char_ingame_name']}" in-game`;
                                        }
                                    } else {
                                        if (is_recieving_user) {
                                            return `You have requested that ${row['from_user_display_name']} sends you contract asking for ${-row['isk']} ISK from "${row['to_char_ingame_name']}" in-game`;
                                        } else {
                                            return `${row['to_char_display_name']} has requested you send a contract asking for ${-row['isk']} ISK  from their character "${row['to_char_ingame_name']}" in-game`;
                                        }
                                    }
                                case "pending":
                                    if (row['isk'] === 0) {
                                        if (row["total_items"] > 0) {
                                            if (is_recieving_user) {
                                                return `${row['from_user_display_name']} has created an in-game contract sending you ${row['total_items']} items to "${row['to_char_ingame_name']}"`;
                                            } else {
                                                return `You have created a contract sending ${row['total_items']} items to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                            }
                                        } else {
                                            return "Invalid Pending Contract for 0 ISK and 0 items."
                                        }
                                    } else if (row['isk'] > 0) {
                                        if (is_recieving_user) {
                                            return `${row['from_user_display_name']} has created an in-game contract sending you ${row['isk']} ISK to "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You have created a contract sending ${row['isk']} isk to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    } else {
                                        if (is_recieving_user) {
                                            return `${row['from_user_display_name']} has created an in-game contract requesting ${row['isk']} ISK from your character "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You have created a contract requesting ${row['isk']} from ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    }
                                case "accepted":
                                    if (row['isk'] === 0) {
                                        if (row["total_items"] > 0) {
                                            if (is_recieving_user) {
                                                return `${row['from_user_display_name']} sent ${row['total_items']} items to "${row['to_char_ingame_name']}"`;
                                            } else {
                                                return `You sent ${row['total_items']} items to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                            }
                                        } else {
                                            return "Invalid Contract for 0 ISK and 0 items."
                                        }
                                    } else if (row['isk'] > 0) {
                                        if (is_recieving_user) {
                                            return `${row['from_user_display_name']} sent you ${row['isk']} ISK to "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You sent ${row['isk']} isk to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    } else {
                                        if (is_recieving_user) {
                                            return `${row['from_user_display_name']} recieved ${row['isk']} ISK from your character "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You recieved ${row['isk']} from ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    }
                                case "rejected":
                                    if (row['isk'] === 0) {
                                        if (row["total_items"] > 0) {
                                            if (is_recieving_user) {
                                                return `REJECTED: Contract from ${row['from_user_display_name']} sending you ${row['total_items']} items to "${row['to_char_ingame_name']}"`;
                                            } else {
                                                return `REJECTED: Contract sending ${row['total_items']} items to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                            }
                                        } else {
                                            return "REJECTED: Invalid Pending Contract for 0 ISK and 0 items."
                                        }
                                    } else if (row['isk'] > 0) {
                                        if (is_recieving_user) {
                                            return `REJECTED: Contract from ${row['from_user_display_name']} sending you ${row['isk']} ISK to "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `REJECTED: Contract sending ${row['isk']} isk to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    } else {
                                        if (is_recieving_user) {
                                            return `REJECTED: Contract from ${row['from_user_display_name']} requesting ${-row['isk']} ISK from your character "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `REJECTED: Contract requesting ${-row['isk']} from ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    }
                                case "cancelled":
                                    if (row['isk'] === 0) {
                                        if (row["total_items"] > 0) {
                                            if (is_recieving_user) {
                                                return `CANCELLED: Contract from ${row['from_user_display_name']} sending you ${row['total_items']} items to "${row['to_char_ingame_name']}"`;
                                            } else {
                                                return `CANCELLED: Contract sending ${row['total_items']} items to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                            }
                                        } else {
                                            return "CANCELLED: Invalid Pending Contract for 0 ISK and 0 items."
                                        }
                                    } else if (row['isk'] > 0) {
                                        if (is_recieving_user) {
                                            return `CANCELLED: Contract from ${row['from_user_display_name']} sending you ${row['isk']} ISK to "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `CANCELLED: Contract sending ${row['isk']} isk to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    } else {
                                        if (is_recieving_user) {
                                            return `CANCELLED: Contract from ${row['from_user_display_name']} requesting ${-row['isk']} ISK from your character "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `CANCELLED: Contract requesting ${-row['isk']} from ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    }
                                default:
                                    return `Unknown contract status.`;
                            }
                        }
                        edit_url = page_data['contract_view_url'].replace("0", row["id"]);
                        return `<a href="${edit_url}">${mad_make()}</a>`;
                    }
                },
                {
                    "data": "from_user_discord_avatar_url", "title": "Avatar",
                    render: function (data, type, row) {
                        return `<img alt="" class="avatar" src="${data}?size=64" style="width: 64px">`
                    }
                },
                {
                    "data": "from_user_display_name", "title": "Contract Sent By", give_filter: true,
                    render: function (data, type, row) {
                        if (page_data["gooseuser_id"] === row["from_user"]) {
                            return "Sent By You";
                        } else {
                            return data;
                        }
                    }
                },
                {
                    "data": "to_char_ingame_name", "title": "Sent To", give_filter: true,
                    render: function (data, type, row) {
                        return `${data} (${row["to_char_display_name"]})`
                    }
                },
                { "data": "created", "title": "Created At" },
                { "data": "system", "title": "In System" },
                { "data": "isk_display", "title": "Isk" },
                {
                    "data": "total_items", "title": "Items",
                    render: function (data, type, row) {
                        edit_url = page_data['contract_view_url'].replace("0", row["id"])
                        return `<a href="${edit_url}">${data} Items</a>`
                    }

                },
                {
                    "data": "id",
                    "title": "Actions",
                    "class": "right-align",
                    "width": "20em",
                    render: function (data, type, row) {
                        function make_buttons(status) {
                            switch (status) {
                                case "requested":
                                    if (page_data["gooseuser_id"] === row["from_user"]) {
                                        return `<a class="pending-btn green-text" href="#">I've Made This Contract</a> / <a class="rejected-btn red-text" href="#">Reject</a>`;
                                    } else {
                                        return '<a class="cancelled-btn grey-text" href="#">Cancel</a>';
                                    }
                                case "pending":
                                    if (page_data["gooseuser_id"] === row["to_char_user_id"]) {
                                        return `<a class="accepted-btn green-text" href="#">I've Accepted This</a> / <a class="rejected-btn red-text" href="#">Reject</a>`;
                                    } else {
                                        return '<a class="cancelled-btn grey-text" href="#">Cancel</a>';
                                    }
                                default:
                                    return ``;
                            }
                        }
                        return `${make_buttons(row["status"])}`;
                    }
                },
                { "data": "isk", "visible": false, },
            ],
        }
    })
    for (var i = 2; i < 9; i++) {
        var column = table.column(i);
        column.visible(!column.visible());
    }
    $('#datatable').on('click', '.pending-btn', Goose.putSubjectAction(table, "contract", "pending"));
    $('#datatable').on('click', '.accepted-btn', Goose.putSubjectAction(table, "contract", "accepted"));
    $('#datatable').on('click', '.rejected-btn', Goose.putSubjectAction(table, "contract", "rejected"));
    $('#datatable').on('click', '.cancelled-btn', Goose.putSubjectAction(table, "contract", "cancelled"));

    function search_func(row, filter_type){
        is_sending_user = page_data["gooseuser_id"] === row["from_user"]
        is_recieving_user = page_data["gooseuser_id"] === row["to_char_user_id"]
        status = row["status"]
        switch(filter_type){
            case "actionable":
                r = is_recieving_user && status === "pending" || is_sending_user && status === "requested";
                return r;
            case "mine":
                return is_sending_user && status === "pending" || is_recieving_user && status === "requested";
            case "old":
                return status !== "pending" && status !== "requested";
            default:
                return true;
        }
    }

    $.fn.dataTable.ext.search.push(
        function( settings, data, dataindex, row ) {
            top_row_data = $("#top_row").data();
            if(top_row_data["filter"]){
                return search_func(row, top_row_data["filter"]);
            } else {
                return true;
            }
        }
    );

    $('#actionable_filter').on('click',  function(){
        $("#top_row").data("filter", "actionable");
        $("#top_row").html("<h3>Your Pending Contracts</h3><p class='red-text'>You have been requested to make or accept the contracts shown below in-game. Please do so and click the action buttons to let the other user know it has happened.");
        table.draw();
        $(".filter").attr("disabled", false);
        $(this).attr("disabled", true);
    }).trigger("click");
    $('#mine_filter').on('click', function(){
        $("#top_row").data("filter", "mine");
        $("#top_row").html("<h3>Contracts You've Requested or Sent</h3>");
        table.draw();
        $(".filter").attr("disabled", false);
        $(this).attr("disabled", true);
    });
    $('#old_filter').on('click', function(){
        $("#top_row").data("filter", "old");
        $("#top_row").html("<h3>Old Contracts</h3>");
        table.draw();
        $(".filter").attr("disabled", false);
        $(this).attr("disabled", true);
    });
});
