import cv2

class WebcamAnalyzer:
    """
    Classe responsável por capturar frames de uma webcam local (USB).
    """
    def __init__(self, device_index=0):
        """
        Inicializa o analisador com o índice do dispositivo da webcam.
        """
        self.device_index = device_index
        self.cap = None

    def open(self):
        """
        Abre a conexão com a webcam local.
        """
        self.cap = cv2.VideoCapture(self.device_index)

    def get_frame(self):
        """
        Captura um frame da webcam local.
        """
        if self.cap is None:
            self.open()
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        """
        Libera o recurso da webcam local.
        """
        if self.cap:
            self.cap.release() 