$(function () {
    Goose = GooseJs()
    table = Goose.datatable(function (page_data, table) {
        const prefix = page_data["latest_checked"] ? "event." : ""
        return {
            order: [[0, "asc"]],
            columns: [
                {
                    "data": prefix + "time", "title": "Time"
                },
                {
                    "data": prefix + "item", "title": "Item Name",
                },
                {
                    "data": prefix + "eve_echoes_market_id", "title": "eve_echoes_market_id"
                },
                {
                    "data": prefix + "unique_user_id", "title": "unique_user_id"
                },
                {
                    "data": prefix + "manual_override_price", "title": "Is A Manual" +
                        " Override"
                },
                {
                    "data": prefix + "buy", "title": "buy"
                },
                {
                    "data": prefix + "sell", "title": "sell"
                },
                {
                    "data": prefix + "highest_buy", "title": "highest_buy"
                },
                {
                    "data": prefix + "lowest_sell", "title": "lowest_sell"
                },
                {
                    "data": prefix + "volume", "title": "volume"
                },
                {
                    "data": prefix + "item_id", "title": "Actions",
                    "class": "right-align",
                    "width": "18em",
                    render: function (data, type, row) {
                        const price_list = page_data["price_list_id"]
                        const graph_url = page_data["graph_url"].replace("0", data)
                        const graph_link = `<a class="edit-btn green-text" href="${graph_url}?price_list=${price_list}&days=14&style=lines">View Graph</a>`
                        const id = prefix === "" ? row['id'] : row['event']['id']
                        const edit_url = page_data["edit_url"].replace("0", id)
                        const edit_link = `<a class="edit-btn" href="${edit_url}">Edit Price</a>`
                         return `${edit_link}/${graph_link}`
                    }
                },
            ]
        }
    }, true)
})
