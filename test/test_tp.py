import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stdout, 
    level=logging.DEBUG)
from topomap.io import TopoMapFactory
from topomap.validation import TopoMapValidator

tm = TopoMapFactory.topo_map('tp_top10nl_small', universe_id = 0, srid = 28992)
validator = TopoMapValidator(tm)
validator.validate()