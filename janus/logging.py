import logging
import os

# set up logging to file - see previous section for more details
logPath = "log"
if not os.path.isdir(logPath):
    os.mkdir(logPath)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s {%(filename)-12s:%(lineno)d} %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
    filename=logPath + "/janus.log",
    filemode="a",
)
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter("%(message)s")
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger().addHandler(console)


logger = logging.getLogger()


def setDebugLogLevel():
    console.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
