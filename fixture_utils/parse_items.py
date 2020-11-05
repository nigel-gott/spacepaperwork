import json
import jsonpickle


def main():
    with open("../misc_data/items.json", "r") as html_file:
        lines = json.load(html_file)
        groups = lines['groups']
        models = []

        item_pk = 0
        item_type_pk = 0
        item_sub_type_pk = 0
        item_sub_sub_type_pk = 0

        for type_info in groups.values():
            models.append({
                "model": "core.itemtype",
                "pk": item_type_pk,
                "fields": {
                    "name": type_info['name'],
                }
            })
            for sub_type in type_info['contents'].values():
                models.append({
                    "model": "core.itemsubtype",
                    "pk": item_sub_type_pk,
                    "fields": {
                        "name": sub_type['name'],
                        "item_type": item_type_pk
                    }
                })
                for sub_sub_type in sub_type['contents'].values():
                    models.append({
                        "model": "core.itemsubsubtype",
                        "pk": item_sub_sub_type_pk,
                        "fields": {
                            "name": sub_sub_type['name'],
                            "item_sub_type": item_sub_type_pk
                        }
                    })
                    for item in sub_sub_type['contents'].values():
                        models.append({
                            "model": "core.item",
                            "pk": item_pk,
                            "fields": {
                                "name": item['name'],
                                "eve_echoes_market_id": item['id'],
                                "item_type": item_sub_sub_type_pk
                            }
                        })
                        item_pk = item_pk + 1

                    item_sub_sub_type_pk = item_sub_sub_type_pk + 1

                item_sub_type_pk = item_sub_type_pk + 1

            item_type_pk = item_type_pk + 1

        with open("../core/fixtures/items.json", "w") as out_file:
            out_file.write(jsonpickle.encode(models, indent=4))


if __name__ == "__main__":
    main()
