
$(function () {
    Goose = GooseJs();
    table = Goose.datatable(function (page_data, table) {
        return {
            order: [[0, "asc"]],
            columns: [
                {
                    "data": "owner_display_name", "title": "Display Name"
                },
                { "data": "corp", "title": "Corp", "give_filter": true },
                { "data": "ingame_name", "title": "In Game Character Name" },
                { "data": "owner_status", "title": "Status", "give_filter": true },
                {
                    "data": "id", "title": "Actions",
                    "class": "right-align",
                    "width": "18em",
                    render: function (data, type, row) {
                        edit_url = page_data["edit_url"].replace("0", data);
                        return `<a class="unknown-btn grey-text" href="#">Move to Unknown</a> / <a class="delete-btn red-text" href="#">Delete</a> / <a class="edit-btn orange-text" href="${edit_url}">Edit</a>`;
                    }
                },
            ]
        }
    })
    $('#datatable').on('click', '.unknown-btn', Goose.putSubjectAction(table, "character", "unknown"));
    $('#datatable').on('click', '.delete-btn', Goose.putSubjectAction(table, "character","delete"));
});
