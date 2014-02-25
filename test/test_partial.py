import logging
import sys
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stderr, 
    level=logging.DEBUG)
from topomap.io import TopoMapFactory
from simplegeom.wkt import loads
from simplegeom.wkb import dumps 

factory = TopoMapFactory()

bbox = loads("""SRID=28992;POLYGON((119000 487000, 122000 487000, 122000 488000, 119000 488000, 119000 487000))""")
#0 0, 400000 0, 400000 650000, 0 650000, 0 0))')

fh = open("/tmp/edges.wkt", "w")
fh.write("id;wkt\n")

tm = factory.topo_map_proper_bbox(name='adam_centre_clean', 
                                  bbox=bbox, 
                                  universe_id=-1, 
                                  srid=28992)
for he in tm.half_edges.itervalues():
    fh.write("{0};{1}\n".format(he.id, he.geometry))

fh.close()

# missing_face = tm.faces[-99]
# for he in tm.half_edges.itervalues():
#     if he.face is missing_face:
#         print he, he.attrs

fh = open("/tmp/faces.wkt", "w")
fh.write("id;wkt\n")
for face in tm.faces.itervalues():
    if not face.unbounded and not face.attrs['locked']:
        fh.write("{0};{1}\n".format(face.id, face.multigeometry()[0]))
fh.close()
