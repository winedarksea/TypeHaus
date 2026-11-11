"""Purchase the same stock lengths and supports the snow-retention resolver draws."""

from typehaus.hardware.catalog import hardware_by_model
from typehaus.hardware.snow_retention import COLORSTRIP, CROSSMEMBER, SNOCLIP, VERSACLIP
from typehaus.model.structure import Connector
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.snow_retention_layout import snow_retention_layout
from typehaus.takeoff.hardware_row import HardwareRow, hardware_row


def snow_retention_rows(model: ResolvedModel) -> list[HardwareRow]:
    rows = []
    for storey in model.plan.storeys:
        for connector in model.plan.storey_elements(storey.tag):
            if not isinstance(connector, Connector) or connector.snow_retention is None:
                continue
            layout, _ = snow_retention_layout(model, connector)
            if layout is None:
                continue  # the resolver reports the invalid authored run
            length_ft = (layout.end - layout.start) / 0.3048
            counts = (
                (CROSSMEMBER.model, len(layout.segments),
                 f"7 ft 8 in stock; {len(layout.segments) - 1} splices used, included with stock"),
                (connector.snow_retention.clamp, len(layout.supports),
                 "one per intersected seam; M8 attachment bolt and two setscrews included"),
                (VERSACLIP.model, len(layout.supports), "one per seam clamp"),
                (SNOCLIP.model, len(layout.snow_clips), "one per full panel bay; screw included"),
                (COLORSTRIP.model, 1, "one 2-inch-wide strip sheared to run length"),
            )
            for part, count, basis in counts:
                if count:
                    rows.append(hardware_row(
                        hardware_by_model(part), scope="snow-retention run", count=count,
                        part_number=part, length_ft=length_ft if part in (
                            CROSSMEMBER.model, COLORSTRIP.model) else None,
                        by_storey={storey.tag: count}, tags=[connector.tag],
                        basis=(f"{connector.tag}: {basis}; provisional, "
                               "supplier drift sizing pending")))
    return rows
