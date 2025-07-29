import cv2

class DvrCFTVAnalyzer:
    """
    Classe responsável por capturar frames de um DVR CFTV via stream RTSP.
    """
    def __init__(self, rtsp_url):
        """
        Inicializa o analisador com a URL RTSP do DVR.
        """
        self.rtsp_url = rtsp_url
        self.cap = None

    def open(self):
        """
        Abre a conexão com o DVR via RTSP.
        """
        self.cap = cv2.VideoCapture(self.rtsp_url)

    def get_frame(self):
        """
        Captura um frame do DVR.
        """
        if self.cap is None:
            self.open()
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        """
        Libera o recurso da câmera.
        """
        if self.cap:
            self.cap.release() 