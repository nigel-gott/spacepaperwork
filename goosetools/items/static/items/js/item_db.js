
$(function () {
    Goose = GooseJs();
    table = Goose.datatable(function (page_data, table) {
        return {
            order: [[0, "asc"]],
            columns: [
                {
                    "data": "name", "title": "Name"
                },
                {
                    "data": "item_type", "title": "Type", "give_filter": true
                },
                {
                    "data": "item_sub_type", "title": "Sub Type", "give_filter": true
                },
                {
                    "data": "item_sub_sub_type", "title": "Sub Sub Type", "give_filter": true
                },
                {
                    "data": "eve_echoes_market_id", "title": "eve_echoes_market_id"
                },
                {
                    "data": "cached_lowest_sell", "title": "cached_lowest_sell"
                },
                {
                    "data": "name", "title": "Actions",
                    "class": "right-align",
                    "width": "18em",
                    render: function (data, type, row) {
                        return '???'
                        // edit_url = page_data["edit_url"].replace("0", data);
                        // return `<a class="unknown-btn grey-text" href="#">Move to Unknown</a> / <a class="delete-btn red-text" href="#">Delete</a> / <a class="edit-btn orange-text" href="${edit_url}">Edit</a>`;
                    }
                },
            ]
        }
    })
    // $('#datatable').on('click', '.unknown-btn', Goose.putSubjectAction(table, "character", "unknown"));
    // $('#datatable').on('click', '.delete-btn', Goose.putSubjectAction(table, "character","delete"));
});
