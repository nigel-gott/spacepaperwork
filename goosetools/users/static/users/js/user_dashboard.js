
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
                    "data": "display_name", "title": "Display Name"
                },
                { "data": "char_names", "title": "Characters" },
                { "data": "status", "title": "Status", "give_filter": true },
                {
                    "data": "sa_profile", "title": "SA Profile",
                    render: function (data, type, row) {
                        if (data) {
                            return `<a href="${data}">Profile</a>`;
                        } else {
                            return "";
                        }
                    }
                },
                { "data": "groups", "title": "Groups", "filter_values": page_data["all_group_names"], "initial_filter_value": page_data["group_filter"] },
                { "data": "notes", "title": "Notes" },
                { "data": "voucher_username", "title": "Voucher", "defaultContent": "" },
                {
                    "data": "uid", "title": "Actions",
                    "class": "right-align",
                    "width": "8em",
                    render: function (data, type, row) {
                        const status = row["status"]
                        switch (status) {
                            case "approved":
                                return `<a class="ban-btn red-text" href="#">Ban</a> / <a class="inactive-btn grey-text" href="#">InActive</a>`;
                            case "unapproved":
                                return '<a class="approve-btn green-text" href="#">Approve</a> / <a class="ban-btn red-text" href="#">Ban</a>';
                            case "rejected":
                                return '<a class="grey-text inactive-btn" href="#">UnBan</a> / <a class="approve-btn green-text" href="#">Approve</a>';
                            default:
                                return `No Actions for ${status}`;
                        }
                    }
                },
            ]
        }
    })
    $('#datatable').on('click', '.ban-btn', Goose.putSubjectAction(table, "gooseuser", "ban"));
    $('#datatable').on('click', '.inactive-btn', Goose.putSubjectAction(table, "gooseuser", "unapprove"));
    $('#datatable').on('click', '.approve-btn', Goose.putSubjectAction(table, "gooseuser", "approve"));
});
