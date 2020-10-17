import csv
import json
import jsonpickle


def main():
    with open("misc_data/systems.csv", "r", newline='') as systems_csv:
        lines = list(csv.reader(systems_csv))[1:]

        region_to_pk = {}

        models = []

        for line in lines:
            region = line[2]
            if region not in region_to_pk:
                region_to_pk[region] = True
                models.append({
                    "model": "core.region",
                    "pk": region,
                    "fields": {
                        "name": region
                    }
                })

        for line in lines:
            region = line[2]
            system = line[4]
            security = line[5]
            jita = int(line[1])
            if jita < 0:
                jita = None
            models.append({
                "model": "core.system",
                "pk": system,
                "fields": {
                    "name": system,
                    "region": region,
                    "jumps_to_jita": jita,
                    "security": security
                }
            })

        with open("core/fixtures/systems.json", "w") as out_file:
            out_file.write(jsonpickle.encode(models, indent=4))


if __name__ == "__main__":
    main()
