"""Generate fixed JPEGs with GPS coordinates and raw XMP region metadata."""

import io
import os
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True)
for name, size, unit in (
    ("landscape", (960, 640), None),
    ("portrait", (640, 960), None),
    ("xmp-no-unit", (960, 640), ""),
    ("xmp-normalized", (960, 640), ' stArea:unit="normalized"'),
):
    width, height = size
    picture = Image.new("RGB", size, "#31557b")
    draw = ImageDraw.Draw(picture)
    draw.rectangle((0, height * 2 // 3, width, height), fill="#405d38")
    draw.rectangle((width * 3 // 8, height * 3 // 10, width * 5 // 8, height * 7 // 10), fill="#edb85d")
    draw.text((24, 24), name, fill="white")
    exif = Image.Exif()
    exif[0x010F] = "Fixture Camera"
    exif[0x0110] = "Fixture Camera"
    exif[0x0132] = "2026:01:01 12:00:00"
    if name == "landscape":
        # Standard GPS IFD: fixed WGS84 test coordinates, 48.85 N / 2.35 E.
        exif[0x8825] = {
            0: b"\x02\x03\x00\x00",
            1: "N",
            2: (48.0, 51.0, 0.0),
            3: "E",
            4: (2.0, 21.0, 0.0),
            18: "WGS-84",
        }
    output = io.BytesIO()
    picture.save(output, format="JPEG", quality=90, exif=exif)
    data = output.getvalue()
    if unit is not None:
        xmp = f'''<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:mwg-rs="http://www.metadataworkinggroup.com/schemas/regions/"
xmlns:stArea="http://ns.adobe.com/xmp/sType/Area#" xmlns:stDim="http://ns.adobe.com/xap/1.0/sType/Dimensions#">
<mwg-rs:Regions rdf:parseType="Resource">
<mwg-rs:AppliedToDimensions stDim:w="{width}" stDim:h="{height}" stDim:unit="pixel"/>
<mwg-rs:RegionList><rdf:Bag><rdf:li rdf:parseType="Resource">
<mwg-rs:Name>Long fixture subject label for a small region</mwg-rs:Name><mwg-rs:Type>Face</mwg-rs:Type>
<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0.25" stArea:h="0.4"{unit}/>
</rdf:li></rdf:Bag></mwg-rs:RegionList></mwg-rs:Regions>
</rdf:Description></rdf:RDF></x:xmpmeta>'''.encode()
        segment = b"http://ns.adobe.com/xap/1.0/\0" + xmp
        data = data[:2] + b"\xff\xe1" + struct.pack(">H", len(segment) + 2) + segment + data[2:]
    photo = destination / f"{name}.jpg"
    photo.write_bytes(data)
    os.utime(photo, (1767268800, 1767268800))
