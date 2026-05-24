"""Type aliases for the various IDFM identifier formats.

Each transport entity (line, stop point, stop area, exchange area) is
identified by a string with a specific format. These aliases document the
expected shape of each identifier so that function signatures and downstream
APIs stay self-explanatory, while remaining plain :class:`str` at runtime.
"""

from typing import TypeAlias


#: Identifier of an *arrêt* (stop point).
#: Format: ``STIF:StopPoint:Q:XXXXX:``.
ArId: TypeAlias = str

#: Identifier of a *zone d'arrêt* (stop area), the parent of one or more
#: :data:`ArId` stop points.
#: Format: ``STIF:StopArea:SP:XXXXX:``.
ZdAId: TypeAlias = str

#: Identifier of a *zone de correspondance* (exchange area), grouping
#: several :data:`ZdAId` stop areas that share an interchange. Integer
#: represented as a string.
ZdCId: TypeAlias = str

#: Short identifier of a transport line, without the SIRI prefix.
#: Format: ``CXXXXX``.
ShortLineId: TypeAlias = str

#: Full identifier of a transport line as returned by the PRIM API.
#: Format: ``STIF:Line::CXXXXX:``. Use
#: :func:`pyidfm.utils.to_short_line_id` to convert to a :data:`ShortLineId`.
LineId: TypeAlias = str
