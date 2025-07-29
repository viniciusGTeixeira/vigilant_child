import cv2

class IPCAMAnalyzer:
    """
    Classe responsável por capturar frames de uma câmera IP (RTSP ou HTTP MJPEG).
    """
    def __init__(self, ipcam_url):
        """
        Inicializa o analisador com a URL da câmera IP.
        """
        self.ipcam_url = ipcam_url
        self.cap = None

    def open(self):
        """
        Abre a conexão com a câmera IP.
        """
        self.cap = cv2.VideoCapture(self.ipcam_url)

    def get_frame(self):
        """
        Captura um frame da câmera IP.
        """
        if self.cap is None:
            self.open()
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        """
        Libera o recurso da câmera IP.
        """
        if self.cap:
            self.cap.release() 