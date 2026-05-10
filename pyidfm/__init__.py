import logging
from pyidfm.types import ArId, ShortLineId, LineId, ZdAId
from pyidfm.utils import to_short_line_id
import requests

from pyidfm.dataset import Dataset
from pyidfm.models import (
    LineData,
    ReportData,
    StopData,
    TrafficData,
    TransportType,
)

TIMEOUT = 60


class IDFMApi:
    def __init__(self, apikey: str, timeout: int = TIMEOUT) -> None:
        # self._session = session
        self._apikey = apikey
        self._timeout = timeout
        self._data = None

    @property
    def data(self) -> Dataset:
        if self._data is None:
            self._data = Dataset()
        return self._data

    def __request(self, url: str, **kwargs) -> dict:
        """
        API request helper for PRIM

        :param url: the url to request
        :return: A json object
        :raise requests.HTTPError: If the HTTP request fails
        """
        response = requests.get(
            url,
            headers={
                "apiKey": self._apikey,
                "Content-Type": "application/json",
                "Accept-encoding": "gzip, deflate",
            },
            params={k: v for k, v in kwargs.items() if v},
            timeout=self._timeout,
        )
        if response.status_code != 200:
            try:
                err = response.json()["Siri"]["ServiceDelivery"][
                    "StopMonitoringDelivery"
                ][0]["ErrorCondition"]["ErrorInformation"]["ErrorText"]
                if (
                    err == "Le couple MonitoringRef/LineRef n'existe pas"
                    or err
                    == "La requête contient des identifiants qui sont inconnus"
                ):
                    raise UnknownIdentifierException()
            except KeyError:
                pass
            response.raise_for_status()
        resp = response.json()["Siri"]["ServiceDelivery"]
        if "GeneralMessageDelivery" in resp:
            resp = resp["GeneralMessageDelivery"][0]
        elif "StopMonitoringDelivery" in resp:
            resp = resp["StopMonitoringDelivery"][0]

        if resp["Status"] == "false":
            return None

        return resp

    def __navitia_request(self, url, **kwargs):
        """
        API request helper for navitia

        :param url: the url to request
        :return: A json object
        :raise UnknownIdentifierException: If navitia returns an unknown identifier
        """
        response = requests.get(
            url,
            headers={
                "apiKey": self._apikey,
                "Content-Type": "application/json",
                "Accept-encoding": "gzip, deflate",
            },
            params=kwargs,
            timeout=self._timeout,
        )
        if response.status_code != 200:
            logging.warning(f"Error while fetching information from {url} - {response.text}")
            return None

        return response.json()


    def get_stops(self, line_id: str) -> list[StopData]:
        """
        Return a list of stop areas corresponding to the specified line

        :param line_id: A string indicating id of a line
        :return: A list of StopData objects
        """
        ret = []
        if line_id in self.data.stops:
            for i in self.data.stops[line_id]:
                ret.append(StopData.from_json(i))
        return ret

    def get_traffic(
        self,
        stop_id: str,
        destination_name: str|None = None,
        direction_name: str|None = None,
        line_id: LineId|None = None,
    ) -> list[TrafficData]:
        """
        Returns the next schedules in a line for a specified depart area to an optional destination

        :param stop_id: A string indicating the id of the depart stop area
        :param destination_name: A string indicating the final destination (I.E. the station name returned by get_directions), the schedules for all the available destinations are returned if not specified
        :param direction_name: A boolean indicating the direction of a train, ignored if not specified
        :param line_id: A string indicating id of a line (if not specified, all schedules for this stop/direction will be returned regardless of the line)
        :return: A list of TrafficData objects
        """

        request = f"https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"
        try:
            response = self.__request(
                request,
                **{
                    "MonitoringRef": stop_id,
                    "LineRef": line_id if line_id else None,
                }
            )
        except UnknownIdentifierException:
            # if the MonitoringRef/LineRef couple does not exists, fallback to use only the MonitoringRef
            logging.debug("unknown MonitoringRef/LineRef couple, falling back to only MonitoringRef")

        ret = []
        for i in response["MonitoredStopVisit"]:
            d = TrafficData.from_json(i)
            if (
                d
                and (direction_name is None or d.direction == direction_name)
                and (destination_name is None or d.destination_name == destination_name)
            ):
                ret.append(d)
        return sorted(ret)

    def get_destinations(
        self,
        stop_id: str|int,
        direction_name: str|None = None,
        line_id: str|None = None,
    ) -> list[str]:
        """
        Returns the available destinations for a specified line

        :param stop_id: A string indicating the id of the depart stop area
        :param direction_name: The direction of a train
        :param line_id: A string indicating id of a line (if not specified, all destinations for this stop will be returned regardless of the line)
        :return: A list of string representing the stations names
        """
        ret = set()
        for i in self.get_traffic(
            stop_id, direction_name=direction_name, line_id=line_id
        ):
            ret.add(i.destination_name)
        return list(ret)

    def get_directions(self, stop_id: str|int, line_id: str|None = None) -> list[str]:
        """
        Returns the available directions for a specified line

        :param stop_id: A string indicating the id of the depart stop area
        :param line_id: A string indicating id of a line (if not specified, all directions for this stop will be returned regardless of the line)
        :return: A list of string representing the stations names
        """
        ret = set()
        for i in self.get_traffic(stop_id, line_id=line_id):
            ret.add(i.direction)
        return list(ret)


    def get_line_reports(self, line_id: str, exclude_elevator: bool = True) -> list[ReportData]:
        """
        Return the traffic informations (usually the current/planned perturbations) for the specified line

        :param line_id: A string indicating the id of a line
        :param exclude_elevator: if the elevator failures perturbations should be ignored
        :return: A list of InfoData objects, the list is empty if no perturbations are registered
        """
        ret = []
        data = self.__navitia_request(
            f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/lines%2Fline%3AIDFM%3A{line_id}/line_reports"
        )
        if data:
            for i in data["disruptions"]:
                if (
                    not exclude_elevator
                    or "tags" not in i
                    or "Ascenseur" not in i["tags"]
                ):
                    ret.append(ReportData.from_json(i))
        return ret

    def get_lines(self, transport: TransportType|None = None) -> list[LineData]:
        """
        Returns the available lines by transport type

        :param transport: the transport type, all of them are returned if this is omitted
        :return: A list of LineData objects
        """
        ret = []
        lines = self.data.get_lines(self._session)
        if transport.value in lines:
            for name, id in lines[transport.value].items():
                ret.append(LineData(name=name, id=id, type=transport))

        return ret

    def get_line(self, line_id: ShortLineId|LineId) -> str|None:
        """
        Returns the line data for a specified line ID

        :param line_id: the line ID to get the data for
        :return: A string representing the line name, or None if the line ID is unknown
        """
        if line_id.startswith("STIF:Line::"):
            line_id = to_short_line_id(line_id)
        line_name = self.data.lines_by_id.get(line_id)
        return line_name

    def get_messages(self,
                     line_id: LineId|None = None,
                     stop_id: ArId|ZdAId|None = None,
                     channel: str|None = None) -> list[str]:
        """
        Return the traffic informations (usually the current/planned perturbations) for the specified line.
        Doc: https://prim.iledefrance-mobilites.fr/fr/apis/idfm-ivtr-info_trafic
        API Doc: blob:https://prim.iledefrance-mobilites.fr/7244f9d2-7208-4b7a-9842-7263087e7355

        :param line_id: A string indicating the id of a line
        :param stop_id: A string indicating the id of a stop
        :param channel: A string indicating the channel of the message (Information, Perturbation or Commercial), all channels are returned if this is omitted
        :return: A list of InfoData objects, the list is empty if no perturbations are registered

        :raise ParameterException: If both line_id and stop_id are specified, as the API does not support
                                   both parameters at the same time
        """
        ret = []

        if line_id is not None and stop_id is not None:
            raise ParameterException("Both line_id and stop_id cannot be specified at the same time")
        if channel is not None:
            if channel not in ["Information", "Perturbation", "Commercial"]:
                raise ParameterException("Channel must be either 'Information', 'Perturbation' or 'Commercial'")

        data = self.__request(
            f"https://prim.iledefrance-mobilites.fr/marketplace/general-message",
            **{
                "LineRef": line_id,
                "StopPointRef": stop_id,
                "InfoChannelRef": channel
            }
        )

        if data:
            for i in data["InfoMessage"]:
                ret.append(i)
        return ret


class UnknownIdentifierException(Exception):
    """
    Exception raised when the identifier (MonitoringRef/LineRef) is unknown
    """

    pass

class ParameterException(Exception):
    """
    Exception raised when invalid parameters are provided
    """
    pass