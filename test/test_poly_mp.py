import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stdout, 
    level=logging.INFO)
log = logging.getLogger(__name__)
from connection import ConnectionFactory
from topomap.io import PolygonFactory
from multiprocessing import Pool

name = "tp_top10nl"
universe_id = 0
srid = 28992

pf = PolygonFactory()
conn = None 

def reconstruct(face_id):
    global conn
    if conn is None:
        conn = ConnectionFactory.connection(True)
    fid, = face_id
    try:
        poly = pf.polygon(name, fid, universe_id=universe_id, srid=srid, connection=conn)
        log.info("Face {0}".format(fid))
    except:
        
        log.error("Problem reconstructing {0}".format(fid))

if __name__ == '__main__':
    connection = ConnectionFactory.connection(False)
    sql = """SELECT 
            face_id::int
        FROM 
            {0}_face
        WHERE 
            face_id <> {1}
        -- ORDER BY 
        --    face_id""".format(name, universe_id)
    pool = Pool() 
    pool.map(reconstruct, connection.irecordset(sql))
