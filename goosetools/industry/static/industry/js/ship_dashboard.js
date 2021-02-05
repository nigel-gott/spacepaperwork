
$(function () {
    Goose = GooseJs();
    table = Goose.datatable(function (page_data, table) {
        return {
            order: [[0, "asc"]],
            columns: [
                {
                    "data": "name", "title": "Name"
                },
                { "data": "free", "title": "Is Free", "give_filter": true },
                { "data": "order_limit_group_name", "title": "Order Limit Group", "defaultContent": "", "give_filter": true },
                {
                    "data": "isk_price", "title": "Isk Price",
                    render: function (data) {
                        return data ? Goose.numberWithCommas(data) : "";
                    }
                },
                {
                    "data": "eggs_price", "title": "Eggs Price",
                    render: function (data) {
                        return data ? Goose.numberWithCommas(data) : "";
                    }
                },
                { "data": "prices_last_updated", "title": "Last Price Update" },
                { "data": "total_order_quantity", "title": "Total Order Quantity" },
                { "data": "total_order_quantity_last_month", "title": "Quantity Last Month" },
                { "data": "last_order", "title": "Last Order Placed On" },
                {
                    "data": "total_isk_and_eggs_quantity", "title": "Total Price",
                    render: function (data) {
                        return data ? Goose.numberWithCommas(data) : "";
                    }
                },
                {
                    "data": "total_isk_and_eggs_quantity_last_month", "title": "Total Price Last Month",
                    render: function (data) {
                        return data ? Goose.numberWithCommas(data) : "";
                    }
                },
                {
                    "data": "id", "title": "Actions",
                    "class": "right-align",
                    "width": "18em",
                    render: function (data, type, row) {
                        return `<a class="waves-btn btn green" href="#">Edit</a>`;
                    }
                },
            ]
        }
    })
    $('#datatable').on('click', '.unknown-btn', Goose.putSubjectAction(table, "character", "unknown"));
    $('#datatable').on('click', '.delete-btn', Goose.putSubjectAction(table, "character", "delete"));
});
