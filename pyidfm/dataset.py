import logging
import json
from pathlib import Path
import requests

from pyidfm.types import ArId, LineId, ShortLineId, ZdAId, ZdCId

DATA_DIR = Path(__file__).parent / "data"

# The various metro, bus, train lines with their ID: CXXXXX and metadata
LINES_FNAME = "lignes.json"
LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"

# Info about the stops and their mapping to lines, with the stop coordinates, city etc
STOP_FNAME = "arrets-lignes.json"
STOP_AND_LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/arrets-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"

# Mapping between stop points (ArRId) and stop areas (ZdAId), and between stop areas and exchange areas (ZdCId)
RELATION_FNAME = "relations.json"
STOP_RELATIONS = "https://data.iledefrance-mobilites.fr/explore/dataset/relations/download/?format=json&timezone=Europe/Berlin&lang=fr"

# Exchange area ID (ZdCId) and their corresponding data (name, coordinates, etc)
EXCHANGE_FNAME = "correspondances.json"
EXCHANGE_AREAS = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/zones-de-correspondance/exports/json?lang=fr&timezone=Europe/Berlin"

# Zone d'Arret (ZdAId) (actual stop area used for train lines as they don't have stop points)
# (Same as the stop_id field in the stops listing, but without the "STIF:StopPoint:Q:" prefix
# and with a "STIF:StopArea:SP:" prefix instead)
ZONE_ARRET_FNAME = "zone-arret.json"
ZONE_ARRET = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/zones-d-arrets/exports/json"


IDFM_DB_LICENCE = "Licence ODbL Version Française"
IDFM_DB_LICENCE_LINK = "http://vvlibri.org/fr/licence/odbl-10/legalcode/unofficial"
IDFM_DB_SOURCES = {
    "Arrêts et lignes associées": "https://data.iledefrance-mobilites.fr/explore/dataset/arrets-lignes",
    "Référentiel des lignes de transport en commun d'île-de-France": "https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes",
    "Référentiel des arrêts : Relations": "https://data.iledefrance-mobilites.fr/explore/dataset/relations",
    "Référentiel des arrêts : Zones de correspondance": "https://data.iledefrance-mobilites.fr/explore/dataset/zones-de-correspondance"
}
IDFM_API_LICENCE = "Licence Mobilité"
IDFM_API_LICENCE_LINK = "https://cloud.fabmob.io/s/eYWWJBdM3fQiFNm"
IDFM_API_LINK = "https://prim.iledefrance-mobilites.fr/fr/donnees-dynamiques/idfm-ivtr-requete_unitaire"


class Dataset:
    """
    Class used to generate the lines and stops listings

    The data is fetched only once per execution, the result is then cached as this process takes multiple seconds

    To find a list of all the stops we need to use multiple datasets:
    LINES
    -> get line ID
    -> STOP_AND_LINES -> get corresponding stops areas for trains (ZdAId) OR get corresponding stops points for other modes (ArRId)
    -> STOP_RELATIONS -> map the ArRid to ZdAId AND map the ZdAId to the exchange area (ZdCId)
    -> EXCHANGE_AREAS -> get the exchange area data

    So the process looks like this: LineID -> ZdAId -> ZdCId OR LineID -> ArId -> ZdAId -> ZdCId
    """

    def __init__(self):
        """
        Fetch and process the data from IDFM datasets
        """
        self.lines: dict[str, dict[str, ShortLineId]] = {}  # mode -> "name" -> line_id
        self.lines_by_id: dict[ShortLineId, str] = {}  # line_id -> name
        self.stops: dict[LineId, list[dict]] = {}  # line_id -> list

        if not DATA_DIR.exists():
            self.update_data()
        else:
            self._load_data()

    def _load_data(self) -> None:
        """
        Load the data from the local JSON files and process it to populate
        the lines and stops listings.
        """
        self.lines.clear()
        self.lines_by_id.clear()
        self.stops.clear()

        line_ids = []
        for l in self.read_json(LINES_FNAME):
            mode = l["fields"]["transportmode"]
            if mode not in self.lines:
                self.lines[mode] = {}

            name = l["fields"]["name_line"]
            if mode == "bus" and "operatorname" in l["fields"]:
                name += " / " + l["fields"]["operatorname"]

            self.lines[mode][name] = l["fields"]["id_line"]
            self.lines_by_id[l["fields"]["id_line"]] = name
            line_ids.append(l["fields"]["id_line"])

        arid_to_zdaid = {}
        zdaid_to_zdcid = {}
        for i in self.read_json(RELATION_FNAME):
            try:
                arid_to_zdaid[i["fields"]["arrid"]] = i["fields"]["zdaid"]
            except KeyError:
                pass
            try:
                zdaid_to_zdcid[i["fields"]["zdaid"]] = i["fields"]["zdcid"]
            except KeyError:
                pass

        zdc = {}
        for i in self.read_json(EXCHANGE_FNAME):
            zdc[i["zdcid"]] = i

        # map line to stops
        stop_ids = {}
        for i in self.read_json(STOP_FNAME):
            id = i["fields"]["id"].split(":")[1]  # strip the IDFM:CXXX prefix
            if id not in self.stops:
                self.stops[id] = []
                stop_ids[id] = []

            if id in line_ids:
                stop_id = i["fields"]["stop_id"]
                if stop_id.find("monomodalStopPlace") == -1:
                    try:
                        stop_id = arid_to_zdaid[stop_id.split(":")[-1]]
                    except KeyError:
                        pass
                else:
                    stop_id = stop_id[24:]

                # try to find the corresponding Exchange Area ID (ZdCId)
                zdcid = zdaid_to_zdcid.get(stop_id)

                if stop_id not in stop_ids[id]:
                    self.stops[id].append(
                        {
                            # Add zone de correspondance info in addition to existing fields
                            "exchange_area_id": None if zdcid is None else "STIF:StopArea:SP:" + zdcid + ":",
                            "exchange_area_name": None if zdcid is None else zdc[zdcid]["zdcname"],
                            "stop_id": "STIF:StopPoint:Q:" + stop_id + ":",
                            "name": i["fields"]["stop_name"],
                            "city": i["fields"]["nom_commune"],
                            "zipCode": i["fields"]["code_insee"],
                            "x": i["fields"]["stop_lat"],
                            "y": i["fields"]["stop_lon"],
                        }
                    )
                    stop_ids[id].append(stop_id)

    def update_data(self) -> None:
        """
        Update the main data JSON from IDFM datasets

        This method can be called to refresh the data if needed,
        as the data is cached in memory after the first fetch.

        :raise requests.HTTPError: If any of the HTTP requests fail
        """
        logging.info("Updating local data with IDFM datasets...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        for url, fname in [
            (LINES, LINES_FNAME),
            (STOP_AND_LINES, STOP_FNAME),
            (STOP_RELATIONS, RELATION_FNAME),
            (EXCHANGE_AREAS, EXCHANGE_FNAME),
            (ZONE_ARRET, ZONE_ARRET_FNAME),
        ]:
            logging.debug(f"Fetching {url}")
            response = requests.get(url)
            response.raise_for_status()
            with open(DATA_DIR / fname, "w") as f:
                f.write(response.text)

        self._load_data()

    @staticmethod
    def read_json(name: str) -> list[dict]:
        with open(DATA_DIR / name, "r") as f:
            return json.load(f)
