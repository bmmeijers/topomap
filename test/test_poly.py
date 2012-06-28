import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stdout, 
    level=logging.DEBUG)
log = logging.getLogger(__name__)
from connection.stateful import irecordset
from topomap.io import PolygonFactory

name = "tp_top10nl"
universe_id = 0
srid = 28992

sql = """SELECT 
            face_id::int
        FROM 
            {}_face
        WHERE 
            face_id <> {}
        -- ORDER BY 
        --    face_id""".format(name, universe_id)
for i, (face_id,) in enumerate(irecordset(sql)):
    if (i % 1000) == 0: print ""
    if (i % 100) == 0: print ".",
    sys.stdout.flush()
    
#    factory = PolygonFactory()
    poly = PolygonFactory.polygon(name, face_id, universe_id=universe_id, srid=srid)
