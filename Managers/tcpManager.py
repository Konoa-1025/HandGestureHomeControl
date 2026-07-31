
#? Managers/tcpManager.py
#? Norifumi Konndo

import Utils.logger as p
import Network.cameraSender as cs
import Network.controlServer as cr
import Network.experimentSender as exp
import Network.logSender as log
import Network.protocol as proto



def Initialization(settings):

    p.info("tcpManagerを初期化中")

    p.success("tcpManagerの初期化完了")

    return True