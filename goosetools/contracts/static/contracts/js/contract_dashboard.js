
$(function () {
    Goose = GooseJs();
    table = Goose.datatable(function (page_data, table) {
        return {
            buttons: [
                {
                    text: 'Toggle Detail Columns',
                    action: function (e, dt, node, config) {
                        for (var i = 0; i < 9; i++) {
                            var column = dt.column(i);
                            column.visible(!column.visible());
                        }
                    }
                }
            ],
            order: [[3, "asc"]],
            columns: [
                {
                    "data": "from_user_display_name", "title": "Contract Info",
                    render: function (data, type, row) {
                        function mad_make() {

                            switch (row["status"]) {
                                case "requested":
                                    if (row['isk'] === 0) {
                                        return "Invalid Requested Contract for 0 ISK."
                                    } else if (row['isk'] > 0) {
                                        if (page_data["gooseuser_id"] === row["to_char"]) {
                                            return `You have requested that ${['from_user_display_name']} sends you ${row['isk']} isk to character "${row['to_char_ingame_name']}" in-game`;
                                        } else {
                                            return `${row['to_char_display_name']} has requested you send ${row['isk']} to their character "${row['to_char_ingame_name']}" in-game`;
                                        }
                                    } else {
                                        if (page_data["gooseuser_id"] === row["to_char"]) {
                                            return `You have requested that ${['from_user_display_name']} sends you contract asking for ${row['isk']} ISK to "${row['to_char_ingame_name']}" in-game`;
                                        } else {
                                            return `${row['to_char_display_name']} has requested you send a contract asking for ${row['isk']} to their character "${row['to_char_ingame_name']}" in-game`;
                                        }
                                    }
                                case "pending":
                                    if (row['isk'] === 0) {
                                        if (row["total_items"] > 0) {
                                            if (page_data["gooseuser_id"] === row["to_char"]) {
                                                return `${['from_user_display_name']} has created an in-game contract sending you ${row['total_items']} items to "${row['to_char_ingame_name']}"`;
                                            } else {
                                                return `You have created a contract sending ${row['total_items']} items to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                            }
                                        } else {
                                            return "Invalid Pending Contract for 0 ISK and 0 items."
                                        }
                                    } else if (row['isk'] > 0) {
                                        if (page_data["gooseuser_id"] === row["to_char"]) {
                                            return `${['from_user_display_name']} has created an in-game contract sending you ${row['isk']} ISK to "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You have created a contract sending ${row['ISK']} isk to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    } else {
                                        if (page_data["gooseuser_id"] === row["to_char"]) {
                                            return `${['from_user_display_name']} has created an in-game contract requesting ${row['isk']} ISK from your character "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You have created a contract requesting ${row['ISK']} from ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    }
                                case "accepted":
                                    if (row['isk'] === 0) {
                                        if (row["total_items"] > 0) {
                                            if (page_data["gooseuser_id"] === row["to_char"]) {
                                                return `${['from_user_display_name']} sent ${row['total_items']} items to "${row['to_char_ingame_name']}"`;
                                            } else {
                                                return `You sent ${row['total_items']} items to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                            }
                                        } else {
                                            return "Invalid Contract for 0 ISK and 0 items."
                                        }
                                    } else if (row['isk'] > 0) {
                                        if (page_data["gooseuser_id"] === row["to_char"]) {
                                            return `${['from_user_display_name']} sent you ${row['isk']} ISK to "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You sent ${row['ISK']} isk to ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    } else {
                                        if (page_data["gooseuser_id"] === row["to_char"]) {
                                            return `${['from_user_display_name']} recieved ${row['isk']} ISK from your character "${row['to_char_ingame_name']}"`;
                                        } else {
                                            return `You recieved ${row['ISK']} from ${row['to_char_ingame_name']}(${row['to_char_display_name']}) in-game`;
                                        }
                                    }
                                case "rejected":
                                    return ``;
                                case "cancelled":
                                    return ``;
                                default:
                                    return ``;
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
                { "data": "status", "title": "Status", "give_filter": true, "initial_filter_value": page_data["status_filter"] },
                {
                    "data": "id",
                    "title": "Actions",
                    "class": "right-align",
                    "width": "20em",
                    render: function (data, type, row) {
                        function make_buttons(status) {
                            switch (status) {
                                case "requested":
                                    return `<a class="ban-btn green-text" href="#">I've Made This Contract</a> / <a class="inactive-btn grey-text" href="#">Cancel</a>`;
                                case "pending":
                                    if (page_data["gooseuser_id"] === row["to_char"]) {
                                        return `<a class="pulse ban-btn green-text" href="#">I've Accepted This</a> / <a class="inactive-btn grey-text" href="#">Reject</a>`;
                                    } else {
                                        return '<a class="ban-btn grey-text" href="#">Cancel</a>';
                                    }
                                default:
                                    return ``;
                            }
                        }
                        return `${make_buttons(row["status"])}`;
                    }
                },
            ]
        }
    })
    for (var i = 1; i < 9; i++) {
        var column = table.column(i);
        column.visible(!column.visible());
    }
    $('#datatable').on('click', '#requested_button', function () {

    });
    $('#datatable').on('click', '.refresh-btn', Goose.putSubjectAction(table, "gooseuser", "refresh", "api", function (response_json) {
        M.toast({ html: response_json["output"] })
    }));
});
