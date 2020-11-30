import csv

import jsonpickle


def main():
    with open("misc_data/ships.csv", "r", newline="") as ships_csv:
        models = []
        lines = list(csv.reader(ships_csv))[1:]

        pk = 0
        invalid_ships = {
            "Impairor",
            "Capsule",
            "Reaper",
            "Ibis",
            "Velator",
            "Xian-Yue Prototype",
            "Xian-Yue",
        }
        for line in lines:
            name = line[0]
            if name in invalid_ships:
                continue
            tech_level = line[7]
            free = int(tech_level) <= 6
            models.append(
                {
                    "model": "industry.ship",
                    "pk": name,
                    "fields": {"name": name, "tech_level": tech_level, "free": free},
                }
            )
            pk = pk + 1

        with open("goosetools/industry/fixtures/ships.json", "w") as out_file:
            out_file.write(jsonpickle.encode(models, indent=4))


if __name__ == "__main__":
    main()
