
$(function () {
    Goose = GooseJs();
    table = Goose.datatable(function (page_data, table) {
        return {
            order: [[0, "asc"]],
            columns: [
                {
                    "data": "discord_avatar_url", "title": "Avatar",
                    render: function (data, type, row) {
                        return `<img alt="" class="avatar" src="${data}?size=64" style="width: 64px">`
                    }
                },
                {
                    "data": "display_name", "title": "Display Name",
                    render: function (data, type, row) {
                        const username = row["username"]
                        var display_name;
                        if (data !== row["username"]) {
                            display_name = `${data} (${username})`;
                        } else {
                            display_name = username;
                        }
                        comment_url = page_data['user_admin_view_url'].replace("0", row["id"])
                        return `<a href="${comment_url}">${display_name}</a>`;
                    }
                },
                { "data": "char_names", "title": "Characters" },
                { "data": "status", "title": "Status", "give_filter": true, "initial_filter_value": page_data["status_filter"] },
                { "data": "groups", "title": "Groups", "filter_values": page_data["all_group_names"], "initial_filter_value": page_data["group_filter"], "include_partial_matches": true, "empty_filter_name": "No Groups" },
                {
                    "data": "notes", "title": "Notes",
                },
                {
                    "data": "id",
                    "title": "Actions",
                    "class": "right-align",
                    "width": "20em",
                    render: function (data, type, row) {
                        function make_ban_buttons(status) {
                            switch (status) {
                                case "approved":
                                    return `<a class="ban-btn red-text" href="#">Ban</a> / <a class="inactive-btn grey-text" href="#">InActive</a>`;
                                case "unapproved":
                                    return '<a class="approve-btn green-text" href="#">Approve</a> / <a class="ban-btn red-text" href="#">Ban</a>';
                                case "rejected":
                                    return '<a class="grey-text inactive-btn" href="#">UnBan</a> / <a class="approve-btn green-text" href="#">Approve</a>';
                                default:
                                    return `Error unknown status: ${status}`;
                            }
                        }
                        comment_url = page_data['user_admin_view_url'].replace("0", data)
                        const status = row["status"]
                        return `<a href="${comment_url}">Admin</a> / <a class="refresh-btn" href="#">Sync Groups</a> / ${make_ban_buttons(status)}`;
                    }
                },
            ]
        }
    })
    $('#datatable').on('click', '.ban-btn', Goose.putSubjectAction(table, "gooseuser", "ban"));
    $('#datatable').on('click', '.inactive-btn', Goose.putSubjectAction(table, "gooseuser", "unapprove"));
    $('#datatable').on('click', '.approve-btn', Goose.putSubjectAction(table, "gooseuser", "approve"));
    $('#datatable').on('click', '.refresh-btn', Goose.putSubjectAction(table, "gooseuser", "refresh", "api", function (response_json) {
        M.toast({ html: response_json["output"] })
    }));
});
