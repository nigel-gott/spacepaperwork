
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
                    "data": "tech_level", "title": "Tech Level", "give_filter": true,
                },
                { "data": "free", "title": "Free (click to change)", "filter_values": ["Free", "Paid For"],
                    render: function (data, type, row) {
                        const text = data ? "Free" : "Paid For";
                        return `<a class="flip-btn" href="#">${text}</a>`
                    }
                },
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
                    "data": "name", "title": "Actions",
                    "class": "right-align",
                    "width": "18em",
                    render: function (data, type, row) {
                        edit_url = page_data["edit_url"].replace("0", data);
                        return `<a class="waves-btn btn green" href="${edit_url}">Edit</a>`;
                    }
                },
            ]
        }
    })
    $('#datatable').on('click', '.flip-btn', Goose.putSubjectAction(table, "ship", "flip_free", "industry/api"));
});
