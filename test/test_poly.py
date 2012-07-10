import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stdout, 
    level=logging.INFO)
log = logging.getLogger(__name__)
from connection.stateful import irecordset, execute
from topomap.io import PolygonFactory

from sink import Schema, Field, dump, dumps, Layer, Index
from sink.bulkload import FileBasedBulkloader

name = "tp_top10nl_small"
universe_id = 0
srid = 28992


edge_id = Field("edge_id", "numeric")
next = Field("next", "numeric")
prev = Field("prev", "numeric")
# rccw = Field("rccw", "numeric")
# rcw = Field("rcw", "numeric")

schema = Schema([edge_id, next, prev])
schema.add_index( Index(fields = [edge_id], primary_key = True) )

man0 = FileBasedBulkloader()
stream0 = man0.stream()

layer = Layer(schema, '{0}_edge_left'.format(name), srid = srid)
sql = dumps(layer)
stream0.write(sql)

layer = Layer(schema, '{0}_edge_right'.format(name), srid = srid)
sql = dumps(layer)
stream0.write(sql)

man0.close()

sql = """SELECT 
            face_id::int
        FROM 
            {0}_face
        WHERE 
            face_id <> {1}
        UNION
        SELECT {1};
        -- ORDER BY 
        --    face_id""".format(name, universe_id)
log.debug(sql)
for i, (face_id,) in enumerate(irecordset(sql)):
    poly = PolygonFactory.wings(name, face_id, universe_id=universe_id, srid=srid)
