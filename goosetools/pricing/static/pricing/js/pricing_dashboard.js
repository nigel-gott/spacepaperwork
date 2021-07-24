$(function () {
    Goose = GooseJs()
    table = Goose.datatable(function (page_data, table) {
        return {
            order: [[0, "asc"]],
            columns: [
                {
                    "data": "id", "title": "Id"
                },
                {
                    "data": "owner",
                    "title": "Owner",
                    "give_filter": true,
                },
                {
                    "data": "api_type",
                    "title": "api_type",
                    "give_filter": true,
                },
                {
                    "data": "price_type",
                    "title": "price_type",
                    "give_filter": true,
                },
                {"data": "name", "title": "Name",
                    render: function (data, type, row) {
                        view_url = page_data["view_url"].replace("0", row['id'])
                        return `<a class="edit-btn green-text" href="${view_url}">${data}</a>`
                    }
                },
                {"data": "id", "title": "Data",
                    render: function (data, type, row) {
                        view_url = page_data["view_data_url"] + "?pricelist_id=" + data
                        return `<a class="edit-btn green-text" href="${view_url}">View Data</a>`
                    }
                },
                {
                    "data": "id", "title": "Actions",
                    "class": "right-align",
                    "width": "18em",
                    render: function (data, type, row) {
                        edit_url = page_data["edit_url"].replace("0", data)
                        return `<a class="edit-btn orange-text" href="${edit_url}">Edit</a>`
                    }
                },
            ]
        }
    })
})
